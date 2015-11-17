#!/usr/bin/env bash

# This script generates language models with KenLM (https://kheafield.com/code/kenlm/) which is included in Moses
#
# Required parameters:
# --moses_dir Absolute path to the mosesdecoder directory
# --output_dir Absolute path to a directory where the language models are written
# --input_dir Absolute path to directory containing the monolingual data, one file per language
#
# Note that Moses must be installed and compiled https://github.com/moses-smt/mosesdecoder
#
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
    -i|--input_dir)
    INPUT_DIR="$2"
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

if [ ! -d "$INPUT_DIR" ]; then
    echo "ERROR: Input directory does not exist"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    echo "ERROR: Output directory does not exist"
    exit 1
fi

CURRENT_DIR=$PWD

cd $INPUT_DIR

for file in $INPUT_DIR/*; do
    name=$(basename "$file")
    if [[ $name =~ true ]]; then
        lang="${name##*.}"
        model="$OUTPUT_DIR/$lang.arpa"
        model_bin="$OUTPUT_DIR/$lang.arpa.bin"
        $MOSES_DIR/bin/lmplz -o 3 < "$name" > "$model"
        # Build binary file
        $MOSES_DIR/bin/build_binary "$model" "$model_bin"
        rm $model
    fi
done

cd $CURRENT_DIR

