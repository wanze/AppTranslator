import urllib
import urllib2
import json
import subprocess
import hashlib
import os
from extractor import ExtractTranslationsFromXML


class Translator(object):
    def get(self, strings, lang_from, lang_to):
        """
        Return the best translation for the given strings
        string -- List of sentences/words given in the source language
        lang_from -- 2-letter language code of source language
        lang_to -- 2-letter language code of target language

        Returns a dictionary
        {
            'translations' : ["Result1", "Result2" ...],
            'debug' : "Debug information"
        }
        """
        raise NotImplementedError

    def get_all(self, strings, lang_from, lang_to):
        """
        Same as "get" but returning all possible translations for each string

        Returns a dictionary
        {
            'translations' : {0 : ["Best", "Second best"], 1: ["Best", "Second best"] ...},
            'debug' : "Debug information"
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

    DEFAULT_CONFIG = {
        'drop_unknown': 0,
        'search_algorithm': 0,
        'max_phrase_length': 20,
        'verbose': 2,
        'stack': 100,
        'tune_weights': 0,
        'weight_d': 0.3,
        'weight_l': 0.5,
        'weight_t': 0.2,
        'weight_w': -1
    }

    def __init__(self, dir_moses, config={}):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)
        self.dir_moses = dir_moses.rstrip('/') + '/'
        dir_data = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self.dir_models = dir_data + 'moses/'
        self.dir_temp = dir_data + 'temp/moses/'
        if not os.path.isdir(self.dir_temp):
            os.makedirs(self.dir_temp)

    def translate_xml(self, xml, lang_from, lang_to):
        e = ExtractTranslationsFromXML(xml)
        translations = e.extract()
        # Write a file with one translation per line that can be processed by Moses
        filename_in = self._get_temp_filename(xml + 'in', lang_from, lang_to)
        self._write_translations_to_file(translations.values(), filename_in)
        filename_debug = self._get_temp_filename(xml + 'debug', lang_from, lang_to)
        cmd = self._get_command(lang_from, lang_to, filename_in, '', filename_debug)
        result = subprocess.check_output(cmd, shell=True)
        dbg = self._get_debug_from_file(filename_debug)
        os.remove(filename_in)
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

    def get_all(self, strings, lang_from, lang_to):
        pass

    def get(self, strings, lang_from, lang_to):
        hash = ''.join(strings)
        file_in = self._get_temp_filename(hash, lang_from, lang_to)
        file_out = self._get_temp_filename(hash + 'out', lang_from, lang_to)
        self._write_translations_to_file(strings, file_in)
        file_debug = self._get_temp_filename(hash + 'debug', lang_from, lang_to)
        cmd = self._get_command(lang_from, lang_to, file_in, file_out, file_debug)
        subprocess.check_output(cmd, shell=True)
        translations = self._read_translations_from_file(file_out)
        dbg = self._get_debug_from_file(file_debug)
        os.remove(file_in)
        return {
            'translations': translations,
            'debug': dbg
        }

    @staticmethod
    def _get_debug_from_file(file_debug):
        dbg = ''
        if os.path.isfile(file_debug):
            dbg = open(file_debug, 'r').read()
            os.remove(file_debug)
        return dbg

    def _get_command(self, lang_from, lang_to, file_input='', file_output='', file_debug=''):
        cmd = self.dir_moses + 'bin/moses -f ' + self.dir_models + lang_from + '-' + lang_to + '/mert-work/moses.ini'
        cmd += self._get_config_command()
        cmd = cmd + ' < ' + file_input if file_input else cmd
        cmd = cmd + ' > ' + file_output if file_output else cmd
        cmd = cmd + ' 2> ' + file_debug if file_debug else cmd
        return cmd

    def _get_config_command(self):
        cmd = ''
        mappings = {
            'weight_w': 'WordPenalty0',
            'weight_l': 'LM0',
            'weight_d': 'Distortion0',
            'weight_t': 'TranslationModel0'
        }
        for key, value in self.config.iteritems():
            if key == 'tune_weights':
                continue
            if not self.config['tune_weights'] and key.startswith('weight'):
                continue
            elif self.config['tune_weights'] and key.startswith('weight'):
                key_new = mappings[key]
                cmd = cmd + " -weight-overwrite '" + key_new + "= " + value + "'"
            else:
                cmd = cmd + ' -' + key.replace('_', '-') + ' ' + str(value)
        return cmd

    def _get_temp_filename(self, string, lang_from, lang_to):
        return self.dir_temp + hashlib.md5(''.join([string, lang_from, lang_to])).hexdigest()

    @staticmethod
    def _write_translations_to_file(translations, filename):
        f = open(filename, 'w')
        for value in translations:
            f.write(value + '\n')
        f.close()

    @staticmethod
    def _read_translations_from_file(filename):
        f = open(filename)
        translations = [value.rstrip() for value in f.read().split('\n')]
        translations.pop()
        os.remove(filename)
        return translations

class TranslatorLamtram(Translator):
    def __init__(self, dir_lamtram, config={}):
        self.dir_lamtram = dir_lamtram.rstrip('/') + '/'
        dir_data = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self.dir_models = dir_data + 'lamtram/'
        self.dir_temp = dir_data + 'temp/lamtram/'
        if not os.path.isdir(self.dir_temp):
            os.makedirs(self.dir_temp)
        self.config = config

    def translate_xml(self, xml, lang_from, lang_to):
        e = ExtractTranslationsFromXML(xml)
        translations = e.extract()
        # Write a file with one translation per line that can be processed by Lamtram
        filename_input = self.get_temp_filename(xml + 'in', lang_from, lang_to)
        file_input = open(filename_input, 'w')
        for key, value in translations.iteritems():
            file_input.write(value + '\n')
        file_input.close()
        cmd = self.get_command(lang_from, lang_to, filename_input)
        result = subprocess.check_output(cmd, shell=True)
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
            'debug': ''
        }

    def get_all(self, string, lang_from, lang_to):
        pass

    def get(self, string, lang_from, lang_to):
        filename = self.get_temp_filename(string, lang_from, lang_to)
        f = open(filename, 'w')
        f.write(string)
        f.close()
        cmd = "echo '" + string + "' | " + self.get_command(lang_from, lang_to, filename)
        result = subprocess.check_output(cmd, shell=True)
        os.remove(filename)
        return {
            'translations': [result.rstrip()],
            'debug': ''
        }

    def get_command(self, lang_from, lang_to, file_input, file_output='', file_debug=''):
        cmd = self.dir_lamtram + 'src/lamtram/lamtram --operation gen --models_in encdec=' + self.dir_models + lang_from + '-' + lang_to + '/transmodel.out --beam 5 --word_pen 0.0 --src_in ' + file_input
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

    def translate_xml(self, xml, lang_from, lang_to):
        pass

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
