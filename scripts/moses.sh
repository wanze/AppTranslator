#!/usr/bin/env bash

# This script generates translation systems for moses for specified languages.
#
# Required parameters:
# --moses_dir Absolute path to the mosesdecoder directory
# --output_dir Absolute path to a directory where the files are written
# --corpus_dir Absolute path to directory containing the monolingual and parallel data of the languages
# --language_models_dir Absolute path to a directory containing the language models
# --languages Language codes of source and target languages to train, separated by a comma, e.g. "fr-en,en-fr,en-de,de-en"
# --mode train|tune (default='train') Start first with mode 'train', afterwards with mode 'tune'
# --run Integer (1,2,3...) -> Specify the run-ID, if parallel data is split up into multiple run directories, e.g. "run-1", "run-2"
#
# For testing, parallel data must be in files "strings-train.clean.<lang_source>" and "strings-train.clean.<lang_target>"
# For tuning, parallel data must be in files "strings-tune.clean.<lang_source>" and "strings-tune.clean.<lang_target>"
#
MODE="train"
RUN=0

while [[ $# > 1 ]]
do
key="$1"
case $key in
    -m|--moses_dir)
    MOSES_DIR="$2"
    shift # past argument
    ;;
    -o|--output_dir)
    OUTPUT_DIR="$2"
    shift # past argument
    ;;
    -lm|--language_models_dir)
    LANGUAGE_MODELS_DIR="$2"
    shift # past argument
    ;;
    -l|--languages)
    IFS=',' read -a LANGUAGES <<< "$2"
    shift # past argument
    ;;
    -m|--mode)
    MODE="$2"
    shift # past argument
    ;;
    -r|--run)
    RUN="$2"
    shift # past argument
    ;;
    -c|--corpus_dir)
    CORPUS_DIR="$2"
    shift # past argument
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

if [ ! -d "$MOSES_DIR" ]; then
    echo "ERROR: Moses not found"
    exit 1
fi

if [ ! -d "$CORPUS_DIR" ]; then
    echo "ERROR: Corpus directory does not exist"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir "$OUTPUT_DIR"
fi

if [ ! -d "$LANGUAGE_MODELS_DIR" ]; then
    echo "ERROR: Language models directory does not exist"
    exit 1
fi

train(){
    local lang_from=$1
    local lang_to=$2
    local corpus_parallel_dir=$3
    nohup nice $MOSES_DIR/scripts/training/train-model.perl -root-dir train -corpus "$corpus_parallel_dir/strings-train.clean" -f "$lang_from" -e "$lang_to" -alignment grow-diag-final-and -reordering msd-bidirectional-fe -cores 4 -lm "0:3:$LANGUAGE_MODELS_DIR/$lang_to.arpa.bin:8" -external-bin-dir "$MOSES_DIR/word_align_tools" -mgiza >& training.out &
}

tune(){
    local lang_from=$1
    local lang_to=$2
    local corpus_parallel_dir=$3
    nohup nice $MOSES_DIR/scripts/training/mert-moses.pl "$corpus_parallel_dir/strings-tune.clean.$lang_from" "$corpus_parallel_dir/strings-tune.clean.$lang_to" "$MOSES_DIR/bin/moses" train/model/moses.ini --mertdir "$MOSES_DIR/bin/" --decoder-flags="-threads 4" &> mert.out &
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
        parallel_dir="parallel"
        if [ "$RUN" -gt 0 ]; then
            parallel_dir="parallel/run-$RUN"
            if [ ! -d "run-$RUN" ]; then
                mkdir "run-$RUN"
            fi
            cd "run-$RUN"
        fi
        corpus_parallel_dir="$CORPUS_DIR/$parallel_dir/$lang1-$lang2"
        if [ ! -d "$corpus_parallel_dir" ]; then
            corpus_parallel_dir="$CORPUS_DIR/$parallel_dir/$lang2-$lang1"
        fi
        if [[ $MODE == "train" ]]; then
            train "$lang1" "$lang2" "$corpus_parallel_dir"
        elif [[ $MODE == "tune" ]]; then
            tune "$lang1" "$lang2" "$corpus_parallel_dir"
        fi
    fi
    cd "$OUTPUT_DIR"
done