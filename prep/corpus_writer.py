import os
import itertools
from extractor import Extractor

class CorpusWriter(object):

    def __init__(self, folder_apks, folder_target, languages):
        """
        folder_apks -- Absolute path to a folder containing the extracted APKs files, one folder per APK
        folder_target -- Target folder where parallel and monolingual data is written
        languages -- List of languages that should be written
        """
        self.folder_apks = folder_apks
        self.folder_target = folder_target
        self.languages = languages

    def write(self):
        for folder_apk in os.listdir(self.folder_apks):
            if folder_apk[0] == '.':
                continue
            extractor = Extractor(os.path.realpath(os.path.join(self.folder_apks, folder_apk)))
            translations = extractor.extract_translations()
            print 'Write monolingual data for app ' + folder_apk
            self._write_monolingual(translations)
            print 'Write billingual data for app ' + folder_apk
            self._write_parallel(translations)

    def _write_monolingual(self, translations):
        folder = os.path.realpath(os.path.join(self.folder_target, 'mono'))
        for language in translations:
            file_mono = os.path.realpath(os.path.join(folder, 'strings.' + language))
            f = open(file_mono, 'a+')
            for key in translations[language]:
                value = translations[language][key]
                if not value:
                    continue
                f.write(value + '\n')
            f.close()

    def _write_parallel(self, translations):
        folder_parallel = os.path.realpath(os.path.join(self.folder_target, 'parallel'))
        langs_available = translations.keys()
        langs = sorted([lang for lang in langs_available if lang in self.languages])
        # We need at least 2 supported languages to create parallel data
        if len(langs) <= 1:
            return
        language_pairs = list(itertools.combinations(langs, 2))
        for language_pair in language_pairs:
            first_lang = language_pair[0]
            second_lang = language_pair[1]
            folder = os.path.realpath(os.path.join(folder_parallel, first_lang + '-' + second_lang))
            if not os.path.isdir(folder):
                os.makedirs(folder)
            file1 = os.path.realpath(os.path.join(folder, 'strings.' + first_lang))
            file2 = os.path.realpath(os.path.join(folder, 'strings.' + second_lang))
            f1 = open(file1, 'a+')
            f2 = open(file2, 'a+')
            for key in translations[first_lang]:
                if key in translations[second_lang]:
                    # Both key exists, we can write the parallel data
                    value1 = translations[first_lang][key]
                    value2 = translations[second_lang][key]
                    if value1 and value2:
                        f1.write(value1 + '\n')
                        f2.write(value2 + '\n')
            f1.close()
            f2.close()


if __name__ == '__main__':
    import sys
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:o:l', ['in=', 'out=', 'languages='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    # Defaults if the script is run without any parameters
    folder_in = os.path.dirname(os.path.realpath(__file__)) + '/../data/translations_extracted'
    folder_out = os.path.dirname(os.path.realpath(__file__)) + '/../data/corpus'
    languages = ['en', 'fr', 'de', 'ru']

    for opt, arg in opts:
        if opt in ('-i', '--in'):
            folder_in = arg
        if opt in ('-o', '--out'):
            folder_out = arg
        if opt in ('-l', '--languages'):
            languages = arg.split(',')

    writer = CorpusWriter(folder_in, folder_out, languages)
    writer.write()