import translations2solr
import solr
import os
import getopt
import sys

class Bleu2Solr(object):
    """
    Create separate cores in Solr for measuring BLEU score
    """

    def __init__(self, files_train, languages, run, solr):
        """
        :param files_train: [source-language-filepath, target-language-filepath]
        :param languages: [source-lang, target-lang]
        :param run: Corresponding run
        :param solr: Instance of Solr class
        """
        self.files_train = files_train
        self.languages = languages
        self.run = run
        self.dir_out = os.path.dirname(files_train[0])
        self.solr = solr

    def index(self):
        """
        Write Solr XML files (stored in same folder as given training data) and index data into Solr
        """
        for i, file_train in enumerate(self.files_train):
            lang = self.languages[i]
            xml_file = self._write_solr_xml(file_train, lang)
            self._index(xml_file, lang)

    def _write_solr_xml(self, file_train, lang):
        xml_file = os.path.join(self.dir_out, lang + '.xml')
        app_id = 'run-' + str(self.run)  # Fake an app ID
        translations = {}
        with open(file_train, 'r') as f:
            for i, sentence in enumerate(f.readlines()):
                translations['key_' + str(i)] = sentence.strip()  # Fake a key
        writer = translations2solr.SolrXMLWriter(xml_file)
        writer.write(app_id, translations)
        return xml_file

    def _index(self, xml_file, lang):
        core = '-'.join(['run', str(self.run), lang])
        self.solr.index(xml_file, core)


if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'l:f:r:s:', ['languages=', 'files_train=', 'run=', 'dir_solr='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    languages = []
    files_train = []
    run = 0
    dir_solr = ''
    for opt, arg in opts:
        if opt in ('-l', '--languages'):
            languages = arg.split(',')
        if opt in ('-f', '--files_train'):
            files_train = arg.split(',')
        if opt in ('-r', '--run'):
            run = arg
        if opt in ('-s', '--dir_solr'):
            dir_solr = arg

    solr = solr.Solr(dir_solr)
    app = Bleu2Solr(files_train, languages, run, solr)
    app.index()
