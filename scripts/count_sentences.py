import getopt
import sys
import os

def count_sentences(file_input):
    with open(file_input, 'r') as f:
        counts = {}
        # Initialize lengths with zeros
        for i in range(10000):
            counts[i] = 0
        for sentence in f:
            n = len(sentence.split()) 
            counts[n] = 1 if n not in counts else counts[n] + 1
        #counts_sorted = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        out = ''
        for length, count in counts.iteritems():
            out = out + str(length) + ';' + str(count) + "\n" 
        return out


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:', ['file='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    f = ''
    for opt, arg in opts:
        if opt in ('-f', '--file'):
            f = arg

    if not os.path.isfile(f):
        print "Input file does not exist"
        sys.exit(2)

    print count_sentences(f)

