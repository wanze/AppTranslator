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
        req = solr.get_top_terms(core, n_terms)
        json_response = json.load(req)
        f = open(os.path.join(output_dir, core + '.csv'), 'w')
        out = ''
        i = 0
        for value in json_response['terms']['value']:
            if i % 2 == 0:
                out = value.encode('utf-8') + ';'
            else:
                out = out + str(value) + "\n"
                f.write(out)
                out = ''
            i += 1
        f.close()
