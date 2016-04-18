#!/usr/bin/env bash

# ./write_bleu_solr.sh en de

source=$1
target=$2
langs="$source-$target"
dir_sources=$langs

if [ ! -d "/home/stefan/AppTranslator/data/corpus_bleu_solr/parallel/$langs" ]; then
	dir_sources="$target-$source"	
fi

#for i in 3 4 5; do
for i in 1 2 3 4 5; do
        mkdir -p "/home/stefan/AppTranslator/data/bleu_score/solr/$langs/run-$i"
        cd "/home/stefan/AppTranslator/data/bleu_score/solr/$langs/run-$i"
	echo "Executing Run-$i"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_solr/parallel/$dir_sources/run-$i/strings-test.clean.$target" "strings-reference.$target"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_solr/parallel/$dir_sources/run-$i/strings-test.clean.$source" "strings-source.$source"
	
	# Create train cores in Solr
	python /home/stefan/AppTranslator/core/bleu2solr.py --languages="$source,$target" --files_train="/home/stefan/AppTranslator/data/corpus_bleu_solr/parallel/$dir_sources/run-$i/strings-train.clean.$source,/home/stefan/AppTranslator/data/corpus_bleu_solr/parallel/$dir_sources/run-$i/strings-train.clean.$target" --dir_solr=/home/stefan/solr-5.3.1 --run="$i"

	python /home/stefan/AppTranslator/core/translator.py --source_lang="$langs-run-$i-$source" --target_lang="$langs-run-$i-$target" --input="strings-source.$source" > "strings-translated.$target"

	/home/stefan/mosesdecoder/scripts/generic/multi-bleu.perl "strings-reference.$target" < "strings-translated.$target" > bleu.txt
done

