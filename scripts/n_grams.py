import getopt
import sys
import os
import nltk
import operator
import string

def get_n_grams(file_input, n, amount):
    with open(file_input, 'r') as f:
        words = nltk.word_tokenize(f.read().translate(None, string.punctuation).decode('utf-8'))
        counts = {}
        for _ngrams in nltk.ngrams(words, n):
	   key = ' '.join(_ngrams)
           counts[key] = 1 if key not in counts else counts[key] + 1
        counts_sorted = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        out = ''
        for ngrams, count in counts_sorted[0:amount]:
          out = out + ngrams + ';' + str(count) + "\n" 
        return out


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:n:', ['file=', 'n=', 'amount='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    n = 1
    f = ''
    amount = 20
    for opt, arg in opts:
        if opt in ('-f', '--file'):
            f = arg
        if opt in ('-n', '--n'):
            n = int(arg)
        if opt in ('-a', '--amount'):
            amount = arg        

    if not os.path.isfile(f):
        print "Input file does not exist"
        sys.exit(2)

    print get_n_grams(f, n, amount)

