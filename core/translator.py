import urllib
import urllib2
import json
import subprocess
import hashlib
import os
import sys
from extractor import Extractor

class Translator(object):
    def get(self, string, lang_from, lang_to):
        """
        Return the best translation for the given string
        string -- Word/Sentence given in the source language
        lang_from -- 2-letter language code of source language
        lang_to -- 2-letter language code of target language

        Returns a dictionary
        {
            'translations' : [Best translation],
            'debug' : Debug information
        }
        """
        raise NotImplementedError

    def get_all(self, string, lang_from, lang_to):
        """
        Same as "get" but returning all possible translations

        Returns a dictionary
        {
            'translations' : <Array of translations>,
            'debug' : Debug information
        }
        """
        raise NotImplementedError

    def translate_xml(self, xml, lang_from, lang_to):
        """
        Translate the given android xml file (containing translations) from the source to the target language
        xml -- Path to android xml file containing strings to translate
        """
        raise NotImplementedError


class TranslatorMoses(Translator):
    def __init__(self, dir_moses, config={}):
        self.dir_moses = dir_moses.rstrip('/') + '/'
        dir_data = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self.dir_models = dir_data + 'moses/'
        self.dir_temp = dir_data + 'temp/moses/'
        self.config = config

    def translate_xml(self, xml, lang_from, lang_to):
        translations = Extractor.get_translations(xml)
        # Write a file with one translation per line that can be processed by Moses
        filename_input = self.get_temp_filename(xml + 'in', lang_from, lang_to)
        file_input = open(filename_input, 'w')
        for key, value in translations.iteritems():
            file_input.write(value + '\n')
        file_input.close()
        filename_debug = self.get_temp_filename(xml + 'debug', lang_from, lang_to)
        cmd = self.get_command(lang_from, lang_to, filename_input, '', filename_debug)
        result = subprocess.check_output(cmd, shell=True)
        dbg = ''
        if os.path.isfile(filename_debug):
            dbg = open(filename_debug, 'r').read()
            os.remove(filename_debug)
        os.remove(filename_input)
        out = []
        i = 0
        trans = result.split('\n')
        for key, value in translations.iteritems():
            row = {
                'key': key,
                'source': value,
                'target': trans[i].strip()
            }
            out.append(row)
            i += 1
        return {
            'translations': out,
            'debug': dbg
        }

    def get_all(self, string, lang_from, lang_to):
        pass

    def get(self, string, lang_from, lang_to):
        file_debug = self.get_temp_filename(string, lang_from, lang_to)
        cmd = "echo '" + string + "' | " + self.get_command(lang_from, lang_to, '', '', file_debug)
        result = subprocess.check_output(cmd, shell=True)
        dbg = ''
        if os.path.isfile(file_debug):
            dbg = open(file_debug, 'r').read()
            os.remove(file_debug)
        return {
            'translations': [result.rstrip()],
            'debug': dbg
        }

    def get_command(self, lang_from, lang_to, file_input='', file_output='', file_debug=''):
        cmd = self.dir_moses + 'bin/moses -f ' + self.dir_models + lang_from + '-' + lang_to + '/train/model/moses.ini -verbose 2'
        cmd = cmd + ' < ' + file_input if file_input else cmd
        cmd = cmd + ' > ' + file_output if file_output else cmd
        cmd = cmd + ' 2> ' + file_debug if file_debug else cmd
        return cmd

    def get_temp_filename(self, string, lang_from, lang_to):
        return self.dir_temp + hashlib.md5(''.join([string, lang_from, lang_to])).hexdigest()


class TranslatorSolr(Translator):
    def __init__(self, url='http://localhost:8983', config={}):
        self.url = url
        self.config = config

    def get_all(self, string, lang_from, lang_to):
        response1 = self._query(string, lang_from)
        # Extract all translation keys from the response dictionary
        keys = self._extract_translation_keys(response1)
        # Perform search in target language based on keys
        translations = []
        debug = {'keys': keys}
        for key in keys:
            response = self._query('key:%s' % key, lang_to)
            if int(response['response']['numFound']) > 0:
                results = [doc['value'][0] for doc in response['response']['docs']]
                debug[key] = results
                translations.extend(results)
        translations = set(translations)
        return {
            'debug': response1,
            'translations': list(translations)
        }

    def get(self, string, lang_from, lang_to):
        pass

    def _query(self, string, lang):
        """
        Query Solr for the given string and language
        """
        query = {'q': string.encode('utf-8')}
        url = self.url + '/solr/' + lang + '/select?' + urllib.urlencode(query) + '&wt=json'
        response = urllib2.urlopen(url)
        return json.loads(response.read())

    @staticmethod
    def _extract_translation_keys(response):
        """
        Parses a json response object from Solr and returns the translation keys of all strings found
        """
        return set([doc['key'][0] for doc in response['response']['docs']])
