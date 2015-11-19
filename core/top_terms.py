import sys
import getopt
import os
import json
from solr import Solr


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'u:o:n:', ['solr_url=', 'output_dir=', 'n_terms='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    solr_url = ''
    output_dir = ''
    n_terms = 10
    for opt, arg in opts:
        if opt in ('-u', '--solr_url'):
            solr_url = arg
        if opt in ('-o', '--output_dir'):
            output_dir = arg
        if opt in ('-n', '--n_terms'):
            n_terms = int(arg)

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    solr = Solr('', solr_url)
    for core in solr.get_cores():
        print "Getting and writing top terms for " + core
        terms = solr.get_top_terms(core, n_terms)
        f = open(os.path.join(output_dir, core + '.csv'), 'w')
        for term in terms:
            f.write(term['value'] + ';' + str(term['count']) + "\n")
        f.close()
