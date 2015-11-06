import os
import re
import getopt
import sys

"""
Returns a list of available languages together with the total count of all extracted APK files.

Usage: 
$ python count_languages.py -f /path/to/folder/containing/extracted/APKfiles > export_file.csv

@author Stefan Wanzenried <stefan.wanzenried@gmail.com>
"""


class APKLanguageCounter:

    GLUE = ";"

    def __init__(self, folder):
        """
        folder -- Absolute path to a folder where the extracted APK files are stored
        """
        self.folder = folder
        self.counts = {'en': 0}

    def execute(self):
        self.parse_folder(self.folder)
        print self.format_output(self.GLUE)

    def parse_folder(self, folder):
        """
        Recursive parses the given folder until we hit the "res" folder containing the translations.
        """
        files = os.listdir(folder)
        for f in files:
            file_abs_path = os.path.realpath(os.path.join(folder, f))  # Build absolute path
            if f == 'res':
                # We are in the "res" folder, this folder contains a values folder per language
                self.count_languages_of_folder(file_abs_path)
            elif os.path.isdir(file_abs_path):
                # Not yet in the "res" folder, go recursive
                self.parse_folder(file_abs_path)

    def count_languages_of_folder(self, folder):
        """
        Count the languages from the given res folder (increment total count in dictionary)
        Note: For simplicity ATM, we assume that the folder "values" contains english strings; this may not be true
        """
        folders = os.listdir(folder)
        self.counts['en'] += 1
        for folder in folders:
            match = re.search('^values-(\w{2})$', folder)
            if match:
                language = match.group(1)
                if language == 'en':
                    continue
                elif language in self.counts:
                    self.counts[language] += 1
                else:
                    self.counts[language] = 1

    def format_output(self, delimiter):
        """
        Return formatted counts per language, separated with a delimiter
        """
        out = ''
        for language, count in self.counts.iteritems():
            out = out + language + delimiter + str(count) + "\n"

        return out.rstrip("\n")


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'f:', ['folder='])
    except getopt.GetoptError:
        print 'count_languages.py -f <folder>'
        sys.exit(2)

    folder = ''
    for opt, arg in opts:
        if opt == '-f':
            folder = arg

    # Default is ../data/translations_extracted
    if not folder:
        folder = os.path.dirname(os.path.realpath(__file__)) + "/../data/translations_extracted"

    if not os.path.isdir(folder):
        print folder + " is not a valid folder"
        sys.exit(2)

    counter = APKLanguageCounter(folder)
    counter.execute()


main()
