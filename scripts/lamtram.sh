#!/usr/bin/env bash

# This script generates translation models for lamtram
#
# Required parameters:
# --lamtram_dir Absolute path to the lamtram directory
# --output_dir Absolute path to a directory where the files are written
# --corpus_dir Absolute path to directory containing the monolingual and parallel data of the languages
# --languages Language codes of source and target languages to train, separated by a comma, e.g. "fr-en,en-fr,en-de,de-en"
# --nodes Number of nodes for the LSTM layer

NODES=10

while [[ $# > 1 ]]
do
key="$1"
case $key in
    -i|--lamtram_dir)
    LAMTRAM_DIR="$2"
    shift # past argument
    ;;
    -o|--output_dir)
    OUTPUT_DIR="$2"
    shift # past argument
    ;;
    -l|--languages)
    IFS=',' read -a LANGUAGES <<< "$2"
    shift # past argument
    ;;
    -c|--corpus_dir)
    CORPUS_DIR="$2"
    shift # past argument
    ;;
    -n|--nodes)
    NODES="$2"
    shift # past argument
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

if [ ! -d "$LAMTRAM_DIR" ]; then
    echo "ERROR: Lamtram not found"
    exit 1
fi

if [ ! -d "$CORPUS_DIR" ]; then
    echo "ERROR: Corpus directory does not exist"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir "$OUTPUT_DIR"
fi

train(){
    local lang_from=$1
    local lang_to=$2
    local corpus_parallel_dir=$3
    nohup nice "$LAMTRAM_DIR/src/lamtram/lamtram-train" --model_type encdec --context 2 --layers "lstm:$NODES:1" --trainer sgd --learning_rate 0.1 --seed 0 --train_src "$corpus_parallel_dir/strings-train.clean.$lang_from" --train_trg "$corpus_parallel_dir/strings-train.clean.$lang_to" --dev_src "$corpus_parallel_dir/strings-tune.clean.$lang_from" --dev_trg "$corpus_parallel_dir/strings-tune.clean.$lang_to" --model_out transmodel.out &
}

cd "$OUTPUT_DIR"

for language in "${LANGUAGES[@]}"; do
    if [[ $language =~ ^([a-z]{2})-([a-z]{2})$ ]]; then
        if [ ! -d "$language" ]; then
            mkdir "$language"
        fi
        cd "$language"
        lang1=${BASH_REMATCH[1]}
        lang2=${BASH_REMATCH[2]}
        corpus_parallel_dir="$CORPUS_DIR/parallel/$lang1-$lang2"
        if [ ! -d "$corpus_parallel_dir" ]; then
            corpus_parallel_dir="$CORPUS_DIR/parallel/$lang2-$lang1"
        fi
        train "$lang1" "$lang2" "$corpus_parallel_dir"
    fi
    cd "$OUTPUT_DIR"
done