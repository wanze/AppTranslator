#!/usr/bin/env bash

# This script writes and prepares corpus data of extracted translations.

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

# Create parallel and mono data from extracted APK translations
echo "Executing corpous_writer.py"
python ../core/prep/corpus_writer.py --in "$INPUT_DIR" --out "$OUTPUT_DIR"

echo "Start preparing parallel data..."
for folder in $OUTPUT_DIR/parallel/*; do
    name=$(basename "$folder")
    echo "$name..."
    cd $OUTPUT_DIR/parallel/$name
    if [[ $name =~ ^([a-z]{2})-([a-z]{2})$ ]]; then
        lang1=${BASH_REMATCH[1]}
        lang2=${BASH_REMATCH[2]}
        for lang in $lang1 $lang2; do
            # Tokenize
            $MOSES_DIR/scripts/tokenizer/tokenizer.perl -l "$lang" < "strings-train.$lang" > "strings-train.tok.$lang"
            $MOSES_DIR/scripts/tokenizer/tokenizer.perl -l "$lang" < "strings-test.$lang" > "strings-test.tok.$lang"
            # Truecasing, requires training to extracte some statistics about the text
            $MOSES_DIR/scripts/recaser/train-truecaser.perl --model "truecase-model.$lang" --corpus "strings-train.tok.$lang"
            $MOSES_DIR/scripts/recaser/train-truecaser.perl --model "truecase-model.$lang" --corpus "strings-test.tok.$lang"
            # Execute truecasing
            $MOSES_DIR/scripts/recaser/truecase.perl --model "truecase-model.$lang" < "strings-train.tok.$lang" > "strings-train.true.$lang"
            $MOSES_DIR/scripts/recaser/truecase.perl --model "truecase-model.$lang" < "strings-test.tok.$lang" > "strings-test.true.$lang"
            rm strings-train.tok.$lang
            rm strings-test.tok.$lang
            rm truecase-model.$lang
            rm strings-train.$lang
            rm strings-test.$lang
        done
        # Cleanup and limit sentences length to 80
        $MOSES_DIR/scripts/training/clean-corpus-n.perl strings-train.true "$lang1" "$lang2" strings-train.clean 1 80
        $MOSES_DIR/scripts/training/clean-corpus-n.perl strings-test.true "$lang1" "$lang2" strings-test.clean 1 80
        rm strings-train.true.$lang1
        rm strings-train.true.$lang2
        rm strings-test.true.$lang1
        rm strings-test.true.$lang2
    fi
done

echo "Preparing parallel corpus data is finished, start preparing monolingual data..."
cd $OUTPUT_DIR/mono
for file in $OUTPUT_DIR/mono/*; do
    name=$(basename "$file")
    lang="${name##*.}"
    # The monolingual data is used to build the language models, tokenizing and truecasing is sufficient
    $MOSES_DIR/scripts/tokenizer/tokenizer.perl -l "$lang" < "strings.$lang" > "strings.tok.$lang"
    $MOSES_DIR/scripts/recaser/train-truecaser.perl --model "truecase-model.$lang" --corpus "strings.tok.$lang"
    $MOSES_DIR/scripts/recaser/truecase.perl --model "truecase-model.$lang" < "strings.tok.$lang" > "strings.true.$lang"
    rm strings.tok.$lang
    rm truecase-model.$lang
    rm strings.$lang
done

cd $CURRENT_DIR

