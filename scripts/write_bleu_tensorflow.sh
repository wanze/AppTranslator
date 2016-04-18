#!/usr/bin/env bash

# ./write_bleu_tensorflow.sh en de

source=$1
target=$2
langs="$source-$target"
dir_sources=$langs

if [ ! -d "/home/stefan/AppTranslator/data/corpus_bleu_tensorflow/parallel/$langs" ]; then
	dir_sources="$target-$source"	
fi

#for i in 1 2 3 4 5
for i in 1 2 3 4 5; do
        mkdir -p "/home/stefan/AppTranslator/data/bleu_score/tensorflow/$langs/run-$i"
        cd "/home/stefan/AppTranslator/data/bleu_score/tensorflow/$langs/run-$i"
	echo "Executing Run-$i"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_tensorflow/parallel/$dir_sources/run-$i/strings-test.clean.$target" "strings-reference.$target"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_tensorflow/parallel/$dir_sources/run-$i/strings-test.clean.$source" "strings-source.$source"
	
	python /home/stefan/AppTranslator/scripts/tflow.py --run "$i" --decode true --source "$source" --target "$target" --data_dir /home/stefan/AppTranslator/data/tensorflow_bleu --num_layers 1 --size 128 --source_vocab_size 40000 --target_vocab_size 40000 < "strings-source.$source" > "strings-translated.$target"

	/home/stefan/mosesdecoder/scripts/generic/multi-bleu.perl "strings-reference.$target" < "strings-translated.$target" > bleu.txt
done

