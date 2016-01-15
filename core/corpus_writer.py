import os
import itertools
from extractor import Extractor
from sets import Set
import utils


class CorpusWriter(object):

    OUT_FILENAME = 'strings'
    FOLDER_PARALLEL = 'parallel'
    FOLDER_MONOLINGUAL = 'mono'

    def __init__(self, folder_apks, folder_target, languages, shuffle=True):
        """
        folder_apks -- Absolute path to a folder containing the extracted APKs files, one folder per APK
        folder_target -- Target folder where parallel and monolingual data is written
        languages -- List of languages that should be written
        shuffle -- If true, shuffle extracted translations for parallel data
        """
        self.folder_apks = folder_apks
        self.folder_target = folder_target
        self.languages = languages
        self.shuffle = shuffle

    def write(self):
        folder_parallel = os.path.realpath(os.path.join(self.folder_target, self.FOLDER_PARALLEL))
        langs_written = Set()
        for folder_apk in os.listdir(self.folder_apks):
            if folder_apk[0] == '.':
                continue
            extractor = Extractor(os.path.realpath(os.path.join(self.folder_apks, folder_apk)))
            translations = extractor.extract_translations()
            print 'Write monolingual data for app ' + folder_apk
            self._write_monolingual(translations)
            print 'Write parallel data for app ' + folder_apk
            langs_available = translations.keys()
            langs = sorted([lang for lang in langs_available if lang in self.languages])
            # We need at least 2 supported languages to create parallel data
            if len(langs) <= 1:
                continue
            language_pairs = list(itertools.combinations(langs, 2))
            # print language_pairs
            self._write_parallel(translations, folder_parallel, language_pairs)
            for pairs in language_pairs:
                langs_written.add(pairs)
        if self.shuffle:
            for langs in langs_written:
                folder = langs[0] + '-' + langs[1]
                file1 = os.path.join(folder_parallel, folder, self.OUT_FILENAME + '.' + langs[0])
                file2 = os.path.join(folder_parallel, folder, self.OUT_FILENAME + '.' + langs[1])
                utils.shuffle_files(file1, file2)


    def _write_monolingual(self, translations):
        folder = os.path.realpath(os.path.join(self.folder_target, self.FOLDER_MONOLINGUAL))
        if not os.path.isdir(folder):
            os.makedirs(folder)
        for language in translations:
            if language not in self.languages:
                continue
            file_mono = os.path.realpath(os.path.join(folder, self.OUT_FILENAME + '.' + language))
            f = open(file_mono, 'a')
            if translations[language]:
                for key in translations[language]:
                    value = translations[language][key]
                    if value:
                        f.write(value + '\n')
            f.close()

    def _write_parallel(self, translations, folder_parallel, language_pairs):
        for language_pair in language_pairs:
            first_lang = language_pair[0]
            second_lang = language_pair[1]
            folder = os.path.realpath(os.path.join(folder_parallel, first_lang + '-' + second_lang))
            if not os.path.isdir(folder):
                os.makedirs(folder)
            file1 = os.path.realpath(os.path.join(folder, self.OUT_FILENAME + '.' + first_lang))
            file2 = os.path.realpath(os.path.join(folder, self.OUT_FILENAME + '.' + second_lang))
            # Language having more translations is considered to be "primary"
            if len(translations[first_lang]) >= len(translations[second_lang]):
                primary_lang = translations[first_lang]
                secondary_lang = translations[second_lang]
                f1 = open(file1, 'a')
                f2 = open(file2, 'a')
            else:
                primary_lang = translations[second_lang]
                secondary_lang = translations[first_lang]
                f1 = open(file2, 'a')
                f2 = open(file1, 'a')
            for key in primary_lang:
                if key in secondary_lang:
                    # Both key exists, we can write the parallel data
                    value1 = primary_lang[key]
                    value2 = secondary_lang[key]
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
    languages = ['en', 'fr', 'de']

    for opt, arg in opts:
        if opt in ('-i', '--in'):
            folder_in = arg
        if opt in ('-o', '--out'):
            folder_out = arg
        if opt in ('-l', '--languages'):
            languages = arg.split(',')

    writer = CorpusWriter(folder_in, folder_out, languages)
    writer.write()
