#!/usr/bin/env bash

# ./write_bleu_moses.sh en de

source=$1
target=$2
langs="$source-$target"
dir_sources=$langs

if [ ! -d "/home/stefan/AppTranslator/data/corpus_bleu_moses/parallel/$langs" ]; then
	dir_sources="$target-$source"	
fi

#for i in 1 2 3 4 5
for i in 1 2 3 4 5; do
        mkdir -p "/home/stefan/AppTranslator/data/bleu_score/moses/$langs/run-$i"
        cd "/home/stefan/AppTranslator/data/bleu_score/moses/$langs/run-$i"
	echo "Executing Run-$i"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_moses/parallel/$dir_sources/run-$i/strings-test.clean.$target" "strings-reference.$target"
	cp "/home/stefan/AppTranslator/data/corpus_bleu_moses/parallel/$dir_sources/run-$i/strings-test.clean.$source" "strings-source.$source"
	
	/home/stefan/mosesdecoder/bin/moses -f "/home/stefan/AppTranslator/data/moses_bleu/$langs/run-$i/mert-work/moses.ini" < "strings-source.$source"  > "strings-translated.$target"

	/home/stefan/mosesdecoder/scripts/generic/multi-bleu.perl "strings-reference.$target" < "strings-translated.$target" > bleu.txt
done

