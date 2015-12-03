import subprocess
import hashlib
import os
from extractor import ExtractTranslationsFromXML
from solr import Solr


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

    @staticmethod
    def _get_temp_filename(string, lang_from, lang_to):
        return hashlib.md5(''.join([string, lang_from, lang_to])).hexdigest()

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
        filename_in = os.path.join(self.dir_temp, self._get_temp_filename(xml + 'in', lang_from, lang_to))
        self._write_translations_to_file(translations.values(), filename_in)
        filename_debug = os.path.join(self.dir_temp, self._get_temp_filename(xml + 'debug', lang_from, lang_to))
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
        file_in = os.path.join(self.dir_temp, self._get_temp_filename(hash, lang_from, lang_to))
        file_out = os.path.join(self._get_temp_filename(hash + 'out', lang_from, lang_to))
        self._write_translations_to_file(strings, file_in)
        file_debug = os.path.join(self.dir_temp, self._get_temp_filename(hash + 'debug', lang_from, lang_to))
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


class TranslatorLamtram(Translator):

    DEFAULT_CONFIG = {
        'beam': 5,
        'word_pen': 0,
    }

    def __init__(self, dir_lamtram, config={}):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)
        self.dir_lamtram = dir_lamtram.rstrip('/') + '/'
        dir_data = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self.dir_models = dir_data + 'lamtram/'
        self.dir_temp = dir_data + 'temp/lamtram/'
        if not os.path.isdir(self.dir_temp):
            os.makedirs(self.dir_temp)

    def translate_xml(self, xml, lang_from, lang_to):
        e = ExtractTranslationsFromXML(xml)
        translations = e.extract()
        # Write a file with one translation per line that can be processed by Lamtram
        filename_input = os.path.join(self.dir_temp, self.get_temp_filename(xml + 'in', lang_from, lang_to))
        self._write_translations_to_file(translations.values(), filename_input)
        cmd = self._get_command(lang_from, lang_to, filename_input)
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

    def get_all(self, strings, lang_from, lang_to):
        pass

    def get(self, strings, lang_from, lang_to):
        hash = ''.join(strings)
        file_in = os.path.join(self.dir_temp, self._get_temp_filename(hash, lang_from, lang_to))
        file_out = os.path.join(self._get_temp_filename(hash + 'out', lang_from, lang_to))
        self._write_translations_to_file(strings, file_in)
        cmd = self._get_command(lang_from, lang_to, file_in, file_out)
        subprocess.check_output(cmd, shell=True)
        translations = self._read_translations_from_file(file_out)
        os.remove(file_in)
        return {
            'translations': translations,
            'debug': ''
        }

    def _get_command(self, lang_from, lang_to, file_input, file_output='', file_debug=''):
        cmd = self.dir_lamtram + 'src/lamtram/lamtram --operation gen --models_in encdec='
        cmd = cmd + self.dir_models + lang_from + '-' + lang_to + '/transmodel.out'
        cmd = cmd + ' --beam ' + str(self.config['beam']) + ' --word_pen ' + str(self.config['word_pen']) + ' --src_in ' + file_input
        cmd = cmd + ' > ' + file_output if file_output else cmd
        cmd = cmd + ' 2> ' + file_debug if file_debug else cmd
        return cmd

    def get_temp_filename(self, string, lang_from, lang_to):
        return self.dir_temp + hashlib.md5(''.join([string, lang_from, lang_to])).hexdigest()


class TranslatorSolr(Translator):
    def __init__(self, url='http://localhost:8983', config={}):
        self.config = config
        self.solr = Solr('', url)

    def get_all(self, string, lang_from, lang_to):
        pass

    def translate_xml(self, xml, lang_from, lang_to):
        translations = []
        e = ExtractTranslationsFromXML(xml)
        strings = e.extract()
        debug = ''
        for key, string in strings.iteritems():
            t = LongestStubstringMatch(string, lang_from, lang_to, self.solr)
            row = {
                'key': key,
                'source': string,
                'target': t.get_translation()
            }
            translations.append(row)
            debug += t.debug
        return {
            'debug': debug,
            'translations': translations
        }


    def get(self, strings, lang_from, lang_to):
        translations = []
        debug = ''
        for string in strings:
            t = LongestStubstringMatch(string, lang_from, lang_to, self.solr)
            translations.append(t.get_translation())
            debug += t.debug
        return {
            'debug': debug,
            'translations': translations
        }


class LongestStubstringMatch(object):

    def __init__(self, string, lang_from, lang_to, solr):
        self.solr = solr
        self.string = string
        self.debug = ''
        self.lang_from = lang_from
        self.lang_to = lang_to

    def get_translation(self):
        # Try to find a translation from the given string
        result = self._translate_substring(self.string)
        if result:
            return result
        # Reduce string from right and try to match substrings
        tokens = self.string.split()
        if len(tokens) == 1:
            return self.string
        words = [tokens[-1]]
        result = ''
        while not result:
            index_last = len(words)
            string = ' '.join(tokens[0:-index_last])
            if string:
                result = self._translate_substring(string)
            if result or index_last == len(tokens):
                # Translate and append all single words
                result_words = []
                for word in reversed(words):
                    w = self._translate_substring(word)
                    if w:
                        result_words.append(w)
                    else:
                        result_words.append(word)
                result += ' '.join(result_words)
            else:
                index_last += 1
                words.append(tokens[-index_last])
        return result


    def _translate_substring(self, string):
        self.debug += 'Translating "%s"\n' % string
        self.debug += 'Try to find exact match in source langauge\n'
        results = self._find_exact(string, self.lang_from)
        for result in results:
            params = {
                'q': 'app_id:%s AND key:%s' % (result['app_id'], result['key'])
            }
            self.debug += 'Found exact match for app_id=%s, key=%s\n' % (result['app_id'], result['key'])
            # Search for a translation with same app_id and key in target language
            translation = self.solr.query(self.lang_to, params)
            if len(translation):
                t = translation[0]['value']
                self.debug += 'Found translation "%s"\n' % t
                return t
        self.debug += 'No translations for target language available\n'
        self.debug += '\n'
        return ''


    def _find_exact(self, string, lang):
        params = {'q': 'value_lc:"%s %s %s"' % (Solr.DELIMITER_START, self._quote(string), Solr.DELIMITER_END)}
        return self.solr.query(lang, params)


    @staticmethod
    def _quote(string):
        string = string.encode('utf-8')
        return string.replace('"', '')


class TranslatorCompare(Translator):
    def __init__(self, config={}, decoder_settings={}):
        self.config = config
        self.decoder_settings = decoder_settings
        self.solr = TranslatorSolr(config['solr_url'], decoder_settings['solr'])
        self.moses = TranslatorMoses(config['moses'], decoder_settings['moses'])
        self.lamtram = TranslatorLamtram(config['lamtram'], decoder_settings['lamtram'])

    def get_all(self, string, lang_from, lang_to):
        pass

    def translate_xml(self, xml, lang_from, lang_to):
        translations = []
        e = ExtractTranslationsFromXML(xml)
        strings = e.extract()
        for key, string in strings.iteritems():
            result_moses = self.moses.get([string], lang_from, lang_to)
            result_lamtram = self.lamtram.get([string], lang_from, lang_to)
            result_solr = self.solr.get([string], lang_from, lang_to)
            results = {
                'key': key,
                'source': string,
                'target_moses': result_moses['translations'][0],
                'target_lamtram': result_lamtram['translations'][0],
                'target_solr': result_solr['translations'][0]
            }
            translations.append(results)
        return {
            'debug': '',
            'translations': translations
        }


    def get(self, strings, lang_from, lang_to):
        translations = []
        for string in strings:
            result_moses = self.moses.get([string], lang_from, lang_to)
            result_lamtram = self.lamtram.get([string], lang_from, lang_to)
            result_solr = self.solr.get([string], lang_from, lang_to)
            results = {
                'source': string,
                'target_moses': result_moses['translations'][0],
                'target_lamtram': result_lamtram['translations'][0],
                'target_solr': result_solr['translations'][0]
            }
            translations.append(results)
        return {
            'debug': '',
            'translations': translations
        }



import getopt
import sys
if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:t:s:', ['input=', 'target=', 'soruce='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    input = ''
    source = 'en'
    target = 'fr'
    for opt, arg in opts:
        if opt in ('-s', '--source'):
            source = arg
        if opt in ('-t', '--target'):
            target = arg
        if opt in ('-i', '--input'):
            input = arg

    trans = TranslatorSolr()
    result = trans.get([input], source, target)
    print result[0]