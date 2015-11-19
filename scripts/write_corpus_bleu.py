import os
import math
import getopt
import sys
import shutil

"""
Prepares the corpus data to evaluate BLEU score of a translation system. The parallel data input files are split into equal
parts that can then be used for separate training/testing to measure BLEU score with cross validation. The script first splits
the parallel input sentences into multiple files. Then a directory "run" for each part is generated, merging the parts again into train-
and test files. One part is always hold back as test data while the other (n-1) parts are merged together producing the training data.

Example output structure:

--/ en-fr
----- strings.clean-1.en
----- strings.clean-2.en
----- strings.clean-3.en
----- strings.clean-1.fr
----- strings.clean-2.fr
----- strings.clean-3.fr
-----/ run-1
-------- strings-train.clean.en
-------- strings-train.clean.fr
-------- strings-test.clean.en
-------- strings-test.clean.fr
-----/ run-2
-------- strings-train.clean.en
-------- strings-train.clean.fr
-------- strings-test.clean.en
-------- strings-test.clean.fr
-----/ run-3
-------- strings-train.clean.en
-------- strings-train.clean.fr
-------- strings-test.clean.en
-------- strings-test.clean.fr

Arguments:
--dir_corpus		Path to the corpus folder containing 'parallel' and 'mono' data
--output_dir        Path to a directory where the output is written
--languages         List of language pairs from the parallel data that should be prepared, e.g. ['de-en', 'de-fr', 'en-fr']
--parts  		    Number of parts the input files are divided into
--tune              If true, one part of the data is reserved for tuning and a file strings-tune.clean.<lang> is added to each run directory

"""
class CorpusWriterBleu:

    def __init__(self, dir_corpus, languages, dir_out, parts, tune=True):
        self.dir_corpus = dir_corpus
        self.languages = languages
        self.dir_out = dir_out
        self.parts = parts
        self.tune = tune

    def write(self):
        for language_pair in self.languages:
            if os.path.isdir(os.path.join(self.dir_corpus, 'parallel', language_pair)):
                self._write_language_pair(language_pair)


    @staticmethod
    def _get_number_of_lines(filepath):
        with open(filepath) as f:
            return sum(1 for _ in f)


    def _split_file(self, filepath, dir_out):
        path, filename = os.path.split(filepath)
        basename, ext = os.path.splitext(filename)
        lines = int(math.ceil(self._get_number_of_lines(filepath) / float(self.parts)))
        with open(filepath, 'r') as f_in:
            k = 1
            try:
                f_out = open(os.path.join(dir_out, '{}-{}{}'.format(basename, k, ext)), 'w')
                for i, line in enumerate(f_in):
                    if i and i % lines == 0:
                        f_out.close()
                        k += 1
                        f_out = open(os.path.join(dir_out, '{}-{}{}'.format(basename, k, ext)), 'w')
                    f_out.write(line)
            finally:
                f_out.close()


    def _write_language_pair(self, language_pair):
        dir_in = os.path.join(self.dir_corpus, 'parallel', language_pair)
        dir_out = os.path.join(self.dir_out, language_pair)
        if not os.path.isdir(dir_out):
            os.makedirs(dir_out)
        for lang in language_pair.split('-'):
            # Split the file into multiple parts
            self._split_file(os.path.join(dir_in, 'strings.clean.' + lang), dir_out)
            # Merge files again
            self._merge_files(dir_out, lang)


    def _merge_files(self, dir_in, lang):
        files = [f for f in os.listdir(dir_in) if os.path.isfile(os.path.join(dir_in, f)) and f.endswith(lang)]
        # Create a directory for each run, if one part is hold back for tuning, use last part
        n_runs = self.parts if self.tune else self.parts + 1
        for i in range(1, n_runs):
            dir_run = os.path.join(dir_in, 'run-' + str(i))
            if not os.path.isdir(dir_run):
                os.makedirs(dir_run)
            filepath_train = os.path.join(dir_run, 'strings-train.clean.' + lang)
            if os.path.isfile(filepath_train):
                os.remove(filepath_train)
            for f in files:
                # All files except the file marked with the current index are used for training, current index = testing
                if f.endswith(str(i) + '.' + lang):
                    # File is used as test -> copy
                    shutil.copy(os.path.join(dir_in, f), os.path.join(dir_run, 'strings-test.clean.' + lang))
                else:
                    # File is merged into training file
                    with open(filepath_train, 'a') as outfile:
                            with open(os.path.join(dir_in, f)) as file_train:
                                for line in file_train:
                                    outfile.write(line)
        # Copy the tune file to all run directories
        if self.tune:
            file_tune = os.path.join(dir_in, 'strings.clean-' + str(self.parts) + '.' + lang)
            for i in range(1, n_runs):
                shutil.copy(file_tune, os.path.join(dir_in, 'run-' + str(i), 'strings-tune.clean.' + lang))


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'c:l:o:p:t:', ['dir_corpus=', 'languages=', 'dir_out=', 'parts=', 'tune='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    dir_corpus = os.path.dirname(os.path.realpath(__file__)) + '/../data/corpus'
    languages = ['en-fr', 'de-en']
    dir_out = ''
    parts = 6
    tune = True
    for opt, arg in opts:
        if opt in ('-c', '--dir_corpus'):
            dir_corpus = arg
        if opt in ('-l', '--languages'):
            languages = arg.split(',')
        if opt in ('-o', '--dir_out'):
            dir_out = arg
        if opt in ('-p', '--parts'):
            parts = int(arg)
        if opt in ('-t', '--tune'):
            tune = arg in ['true', 'True', '1']

    if not os.path.isdir(dir_corpus):
        print "Corpus directory does not exist!"
        sys.exit(2)

    if dir_out and not os.path.isdir(dir_out):
        os.makedirs(dir_out)

    writer = CorpusWriterBleu(dir_corpus, languages, dir_out, parts, tune)
    writer.write()
