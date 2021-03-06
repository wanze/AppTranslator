# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""
See the following papers for more information on neural translation models.
 * http://arxiv.org/abs/1409.3215
 * http://arxiv.org/abs/1409.0473
 * http://arxiv.org/pdf/1412.2007v2.pdf

Modified version of this file: https://raw.githubusercontent.com/tensorflow/tensorflow/master/tensorflow/models/rnn/translate/translate.py

Usage:
This script is used to generate translation models with tensorflow and decode sentences.

Generating models:
$ nohup python tflow.py --source en --target fr --data_dir /home/stefan/AppTranslator/data/tensorflow --corpus_dir /home/stefan/AppTranslator/data/corpus &

Decoding:
$ python tflow.py --decode true --source en --target fr --data_dir /home/stefan/AppTranslator/data/tensorflow < test.en > out.txt

Parameters:
--source                    Source language
--target                    Target language
--data_dir                  Output directory, where data and models are written
--corpus_idr                Corpus directory, containing parallel data
--size                      Size of network [default=1024]
--num_layers                Number of layers in the model [default=3]
--steps_per_checkpoint      How many training steps to do per checkpoint [default=200]
--decode                    Set this flag to translate an input file, one sentence per line
--replace_unknown           Set to true to replace unknown words with original input [default=True]
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import math
import os
import random
import sys
import time
import tensorflow.python.platform
import numpy as np
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf
from tensorflow.models.rnn.translate import data_utils
from tensorflow.models.rnn.translate import seq2seq_model
from tensorflow.python.platform import gfile

tf.app.flags.DEFINE_float("learning_rate", 0.5, "Learning rate.")
tf.app.flags.DEFINE_float("learning_rate_decay_factor", 0.99,
                          "Learning rate decays by this much.")
tf.app.flags.DEFINE_float("max_gradient_norm", 5.0,
                          "Clip gradients to this norm.")
tf.app.flags.DEFINE_integer("batch_size", 64,
                            "Batch size to use during training.")
tf.app.flags.DEFINE_integer("size", 1024, "Size of each model layer.")
tf.app.flags.DEFINE_integer("num_layers", 3, "Number of layers in the model.")
tf.app.flags.DEFINE_integer("source_vocab_size", 40000, "Source vocabulary size.")
tf.app.flags.DEFINE_integer("target_vocab_size", 40000, "Target vocabulary size.")
tf.app.flags.DEFINE_string("data_dir", "/tmp", "Data directory")
tf.app.flags.DEFINE_string("train_dir", "/tmp", "Training directory.")
tf.app.flags.DEFINE_integer("max_train_data_size", 0,
                            "Limit on the size of training data (0: no limit).")
tf.app.flags.DEFINE_integer("steps_per_checkpoint", 200,
                            "How many training steps to do per checkpoint.")
tf.app.flags.DEFINE_boolean("decode", False,
                            "Set to True for interactive decoding.")
tf.app.flags.DEFINE_boolean("self_test", False,
                            "Run a self-test if this is set to True.")

tf.app.flags.DEFINE_string("source", "en", "Source language")
tf.app.flags.DEFINE_string("target", "fr", "Target language")
tf.app.flags.DEFINE_string("corpus_dir", "", "Corpus directory where monolingual and parallel data is stored")
tf.app.flags.DEFINE_integer("run", -1, "Run")
tf.app.flags.DEFINE_boolean("replace_unknown", True, "Replace unknown words (not in vocabulary) by original word")

FLAGS = tf.app.flags.FLAGS

# We use a number of buckets and pad to the closest one for efficiency.
# See seq2seq_model.Seq2SeqModel for details of how they work.
_buckets = [(5, 10), (10, 15), (20, 25), (40, 50)]


def read_data(source_path, target_path, max_size=None):
    """Read data from source and target files and put into buckets.

  Args:
    source_path: path to the files with token-ids for the source language.
    target_path: path to the file with token-ids for the target language;
      it must be aligned with the source file: n-th line contains the desired
      output for n-th line from the source_path.
    max_size: maximum number of lines to read, all other will be ignored;
      if 0 or None, data files will be read completely (no limit).

  Returns:
    data_set: a list of length len(_buckets); data_set[n] contains a list of
      (source, target) pairs read from the provided data files that fit
      into the n-th bucket, i.e., such that len(source) < _buckets[n][0] and
      len(target) < _buckets[n][1]; source and target are lists of token-ids.
  """
    data_set = [[] for _ in _buckets]
    with gfile.GFile(source_path, mode="r") as source_file:
        with gfile.GFile(target_path, mode="r") as target_file:
            source, target = source_file.readline(), target_file.readline()
            counter = 0
            while source and target and (not max_size or counter < max_size):
                counter += 1
                if counter % 100000 == 0:
                    print("  reading data line %d" % counter)
                    sys.stdout.flush()
                source_ids = [int(x) for x in source.split()]
                target_ids = [int(x) for x in target.split()]
                target_ids.append(data_utils.EOS_ID)
                for bucket_id, (source_size, target_size) in enumerate(_buckets):
                    if len(source_ids) < source_size and len(target_ids) < target_size:
                        data_set[bucket_id].append([source_ids, target_ids])
                        break
                source, target = source_file.readline(), target_file.readline()
    return data_set


def create_model(session, forward_only):
    """Create translation model and initialize or load parameters in session."""
    model = seq2seq_model.Seq2SeqModel(
        FLAGS.source_vocab_size, FLAGS.target_vocab_size, _buckets,
        FLAGS.size, FLAGS.num_layers, FLAGS.max_gradient_norm, FLAGS.batch_size,
        FLAGS.learning_rate, FLAGS.learning_rate_decay_factor,
        forward_only=forward_only)
    model_dir = os.path.join(_get_base_output_dir(), 'model')
    ckpt = tf.train.get_checkpoint_state(model_dir)
    if ckpt and gfile.Exists(ckpt.model_checkpoint_path):
        if not forward_only:
            print("Reading model parameters from %s" % ckpt.model_checkpoint_path)
        model.saver.restore(session, ckpt.model_checkpoint_path)
    else:
        if not forward_only:
            print("Created model with fresh parameters.")
        session.run(tf.initialize_all_variables())
    return model


def _get_base_output_dir():
    run = 'run-' + str(FLAGS.run) if FLAGS.run > 0 else ''
    return os.path.join(FLAGS.data_dir, FLAGS.source + '-' + FLAGS.target, str(FLAGS.num_layers) + '-' + str(FLAGS.size), run)

def _get_model_output_dir():
    return os.path.join(_get_base_output_dir(), 'model')

def _get_data_output_dir():
    return os.path.join(_get_base_output_dir(), 'data')

def simple_tokenizer(sentence):
    """ Our corpus is already tokenized, so this tokenizer just splits at spaces """
    return sentence.split()

def train():
    run = 'run-' + str(FLAGS.run) if FLAGS.run > 0 else ''
    corpus_path = os.path.join(FLAGS.corpus_dir, 'parallel', FLAGS.source + '-' + FLAGS.target, run)
    if not os.path.isdir(corpus_path):
        corpus_path = os.path.join(FLAGS.corpus_dir, 'parallel', FLAGS.target + '-' + FLAGS.source, run)
    data_dir = _get_data_output_dir()
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
    train_path = data_dir
    dev_path = data_dir
    model_dir = _get_model_output_dir()
    if not os.path.isdir(model_dir):
        os.makedirs(model_dir)

    # Create vocabularies of the appropriate sizes.
    target_vocab_path = os.path.join(data_dir, "vocab%d.%s" % (FLAGS.target_vocab_size, FLAGS.target))
    source_vocab_path = os.path.join(data_dir, "vocab%d.%s" % (FLAGS.source_vocab_size, FLAGS.source))
    data_utils.create_vocabulary(target_vocab_path, os.path.join(corpus_path, "strings-train.clean." + FLAGS.target), FLAGS.target_vocab_size, simple_tokenizer)
    data_utils.create_vocabulary(source_vocab_path, os.path.join(corpus_path, "strings-train.clean." + FLAGS.source), FLAGS.source_vocab_size, simple_tokenizer)

    # Create token ids for the training data.
    target_train_ids_path = os.path.join(train_path + (".ids%d.%s" % (FLAGS.target_vocab_size, FLAGS.target)))
    source_train_ids_path = os.path.join(train_path + (".ids%d.%s" % (FLAGS.source_vocab_size, FLAGS.source)))
    data_utils.data_to_token_ids(os.path.join(corpus_path, "strings-train.clean." + FLAGS.target), target_train_ids_path, target_vocab_path)
    data_utils.data_to_token_ids(os.path.join(corpus_path, "strings-train.clean." + FLAGS.source), source_train_ids_path, source_vocab_path)

    # Create token ids for the development data.
    target_dev_ids_path = os.path.join(dev_path + (".ids%d.%s" % (FLAGS.target_vocab_size, FLAGS.target)))
    source_dev_ids_path = os.path.join(dev_path + (".ids%d.%s" % (FLAGS.source_vocab_size, FLAGS.source)))
    data_utils.data_to_token_ids(os.path.join(corpus_path, "strings-dev.clean." + FLAGS.target), target_dev_ids_path, target_vocab_path)
    data_utils.data_to_token_ids(os.path.join(corpus_path, "strings-dev.clean." + FLAGS.source), source_dev_ids_path, source_vocab_path)

    with tf.Session() as sess:
        # Create model.
        print("Creating %d layers of %d units." % (FLAGS.num_layers, FLAGS.size))
        model = create_model(sess, False)

        # Read data into buckets and compute their sizes.
        print("Reading development and training data (limit: %d)."
              % FLAGS.max_train_data_size)
        dev_set = read_data(source_dev_ids_path, target_dev_ids_path)
        train_set = read_data(source_train_ids_path, target_train_ids_path, FLAGS.max_train_data_size)
        train_bucket_sizes = [len(train_set[b]) for b in xrange(len(_buckets))]
        train_total_size = float(sum(train_bucket_sizes))

        # A bucket scale is a list of increasing numbers from 0 to 1 that we'll use
        # to select a bucket. Length of [scale[i], scale[i+1]] is proportional to
        # the size if i-th training bucket, as used later.
        train_buckets_scale = [sum(train_bucket_sizes[:i + 1]) / train_total_size
                               for i in xrange(len(train_bucket_sizes))]

        # This is the training loop.
        step_time, loss = 0.0, 0.0
        current_step = 0
        previous_losses = []
        while True:
            # Choose a bucket according to data distribution. We pick a random number
            # in [0, 1] and use the corresponding interval in train_buckets_scale.
            random_number_01 = np.random.random_sample()
            bucket_id = min([i for i in xrange(len(train_buckets_scale))
                             if train_buckets_scale[i] > random_number_01])

            # Get a batch and make a step.
            start_time = time.time()
            encoder_inputs, decoder_inputs, target_weights = model.get_batch(
                train_set, bucket_id)
            _, step_loss, _ = model.step(sess, encoder_inputs, decoder_inputs,
                                         target_weights, bucket_id, False)
            step_time += (time.time() - start_time) / FLAGS.steps_per_checkpoint
            loss += step_loss / FLAGS.steps_per_checkpoint
            current_step += 1

            # Once in a while, we save checkpoint, print statistics, and run evals.
            if current_step % FLAGS.steps_per_checkpoint == 0:
                # Print statistics for the previous epoch.
                perplexity = math.exp(loss) if loss < 300 else float('inf')
                print("global step %d learning rate %.4f step-time %.2f perplexity "
                      "%.2f" % (model.global_step.eval(), model.learning_rate.eval(),
                                step_time, perplexity))
                # Decrease learning rate if no improvement was seen over last 3 times.
                if len(previous_losses) > 2 and loss > max(previous_losses[-3:]):
                    sess.run(model.learning_rate_decay_op)
                previous_losses.append(loss)
                # Save checkpoint and zero timer and loss.
                # checkpoint_path = os.path.join(FLAGS.train_dir, "translate.ckpt")
                checkpoint_path = os.path.join(model_dir, "translate.ckpt")
                model.saver.save(sess, checkpoint_path, global_step=model.global_step)
                step_time, loss = 0.0, 0.0
                # Run evals on development set and print their perplexity.
                for bucket_id in xrange(len(_buckets)):
                    encoder_inputs, decoder_inputs, target_weights = model.get_batch(
                        dev_set, bucket_id)
                    _, eval_loss, _ = model.step(sess, encoder_inputs, decoder_inputs,
                                                 target_weights, bucket_id, True)
                    eval_ppx = math.exp(eval_loss) if eval_loss < 300 else float('inf')
                    print("  eval: bucket %d perplexity %.2f" % (bucket_id, eval_ppx))
                sys.stdout.flush()


def decode():
    with tf.Session() as sess:
        # Create model and load parameters.
        model = create_model(sess, True)
        model.batch_size = 1  # We decode one sentence at a time.

        # Load vocabularies.
        source_vocab_path = os.path.join(_get_data_output_dir(),
                                     "vocab%d.%s" % (FLAGS.source_vocab_size, FLAGS.source))
        target_vocab_path = os.path.join(_get_data_output_dir(),
                                     "vocab%d.%s" % (FLAGS.target_vocab_size, FLAGS.target))
        source_vocab, _ = data_utils.initialize_vocabulary(source_vocab_path)
        _, target_vocab = data_utils.initialize_vocabulary(target_vocab_path)

        for sentence in sys.stdin:
            sentence = sentence.rstrip('\n')
            # Get token-ids for the input sentence.
            token_ids = data_utils.sentence_to_token_ids(sentence, source_vocab, None, False)

            # Quit early...
            if not len(token_ids):
                print('')
                continue

            # Save unknown words in list
            unknown_words = []
            if FLAGS.replace_unknown:
                words = data_utils.basic_tokenizer(sentence)
                for i, token_id in enumerate(token_ids):
                    if token_id == data_utils.UNK_ID:
                        unknown_words.append(words[i])

            bucket_list = [b for b in xrange(len(_buckets)) if _buckets[b][0] > len(token_ids)]
            if not len(bucket_list):
                print('')
                continue

            # Which bucket does it belong to?
            bucket_id = min(bucket_list)
            # Get a 1-element batch to feed the sentence to the model.
            encoder_inputs, decoder_inputs, target_weights = model.get_batch(
                {bucket_id: [(token_ids, [])]}, bucket_id)
            # Get output logits for the sentence.
            _, _, output_logits = model.step(sess, encoder_inputs, decoder_inputs,
                                             target_weights, bucket_id, True)
            # This is a greedy decoder - outputs are just argmaxes of output_logits.
            outputs = [int(np.argmax(logit, axis=1)) for logit in output_logits]
            # If there is an EOS symbol in outputs, cut them at that point.
            if data_utils.EOS_ID in outputs:
                outputs = outputs[:outputs.index(data_utils.EOS_ID)]
            # Print out sentence corresponding to outputs.
            if not FLAGS.replace_unknown:
                print(" ".join([target_vocab[output] for output in outputs]))
            else:
                # We replace each unknown word in the order they appeared in the input sentence
                words = []
                prev_token_id = -1
                for output in outputs:
                    if output == data_utils.UNK_ID:
                        if len(unknown_words):
                            words.append(unknown_words.pop(0))
                    else:
                        o = target_vocab[output]
                        # Hack alert!!
                        if prev_token_id == data_utils.UNK_ID and o == ';':
                            pass
                        else:
                            words.append(o)
                    prev_token_id = output
                print(" ".join(words).strip())


def self_test():
    """Test the translation model."""
    with tf.Session() as sess:
        print("Self-test for neural translation model.")
        # Create model with vocabularies of 10, 2 small buckets, 2 layers of 32.
        model = seq2seq_model.Seq2SeqModel(10, 10, [(3, 3), (6, 6)], 32, 2,
                                           5.0, 32, 0.3, 0.99, num_samples=8)
        sess.run(tf.initialize_all_variables())

        # Fake data set for both the (3, 3) and (6, 6) bucket.
        data_set = ([([1, 1], [2, 2]), ([3, 3], [4]), ([5], [6])],
                    [([1, 1, 1, 1, 1], [2, 2, 2, 2, 2]), ([3, 3, 3], [5, 6])])
        for _ in xrange(5):  # Train the fake model for 5 steps.
            bucket_id = random.choice([0, 1])
            encoder_inputs, decoder_inputs, target_weights = model.get_batch(
                data_set, bucket_id)
            model.step(sess, encoder_inputs, decoder_inputs, target_weights,
                       bucket_id, False)


def main(_):
    if FLAGS.self_test:
        self_test()
    elif FLAGS.decode:
        decode()
    else:
        train()


if __name__ == "__main__":
    tf.app.run()
