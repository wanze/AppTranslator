import subprocess
import hashlib
import os
from extractor import ExtractTranslationsFromXML
from solr import Solr
import utils
import operator


class Translator(object):
    def get_id(self):
        """
        Return a unique ID for this translator
        """
        raise NotImplementedError

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
        return hashlib.md5(''.join([utils.to_ascii(string), lang_from, lang_to])).hexdigest()

    @staticmethod
    def _write_translations_to_file(translations, filename):
        f = open(filename, 'w')
        for value in translations:
            f.write(utils.to_utf8(value) + '\n')
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

    def get_id(self):
        return 'moses'

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

    def get_id(self):
        return 'lamtram'

    def translate_xml(self, xml, lang_from, lang_to):
        e = ExtractTranslationsFromXML(xml)
        translations = e.extract()
        # Write a file with one translation per line that can be processed by Lamtram
        filename_input = os.path.join(self.dir_temp, self._get_temp_filename(xml + 'in', lang_from, lang_to))
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
        file_out = os.path.join(self.dir_temp, self._get_temp_filename(hash + 'out', lang_from, lang_to))
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
        cmd = cmd + ' --beam ' + str(self.config['beam']) + ' --word_pen ' + str(
                self.config['word_pen']) + ' --src_in ' + file_input
        cmd = cmd + ' > ' + file_output if file_output else cmd
        cmd = cmd + ' 2> ' + file_debug if file_debug else cmd
        return cmd


class TranslatorTensorflow(Translator):
    DEFAULT_CONFIG = {
        'num_layers': 3,
        'size': 1024,
    }

    def __init__(self, config={}):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)
        dir_data = os.path.dirname(os.path.realpath(__file__)) + '/../data/'
        self.dir_models = dir_data + 'tensorflow/'
        self.dir_temp = dir_data + 'temp/tensorflow/'
        if not os.path.isdir(self.dir_temp):
            os.makedirs(self.dir_temp)

    def get_id(self):
        return 'tensorflow'

    def translate_xml(self, xml, lang_from, lang_to):
        e = ExtractTranslationsFromXML(xml)
        translations = e.extract()
        # Write a file with one translation per line that can be processed by Lamtram
        filename_input = os.path.join(self.dir_temp, self._get_temp_filename(xml + 'in', lang_from, lang_to))
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
        file_out = os.path.join(self.dir_temp, self._get_temp_filename(hash + 'out', lang_from, lang_to))
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
        script = os.path.dirname(os.path.realpath(__file__)) + '/../scripts/tflow.py'
        cmd = 'python ' + script + ' --source ' + lang_from + ' --target ' + lang_to + ' --decode true'
        cmd = cmd + ' --size ' + str(self.config['size']) + ' --num_layers ' + str(self.config['num_layers'])
        cmd = cmd + ' --data_dir ' + self.dir_models
        cmd = cmd + ' < ' + file_input
        cmd = cmd + ' > ' + file_output if file_output else cmd
        cmd = cmd + ' 2> ' + file_debug if file_debug else cmd
        return cmd


class SolrBaselineSystem(object):
    def __init__(self, solr, config):
        self.cache = {}
        self.config = config
        self.solr = solr

    def translate(self, string, source, target):
        debug = 'Looking for direct match translations for string "%s"' % string
        string = string.strip()
        translations = self._get_translations(string, source, target)
        if len(translations):
            debug += '\nFound direct translations: ' + str(translations)
            return translations[0]['value'], debug
        # No direct translations available, translate by longest substring of sentence
        words = string.split()
        if len(words) == 1:
            # String was a single word and we didn't get a translation before, we can't do any better
            return string, debug
        debug += '\nNo direct translations found, starting the substring algorithm...'
        translated_substrings, info = self._get_translations_substrings(1, words, source, target)
        debug += info
        translated_substrings = [utils.to_utf8(word) for word in translated_substrings]
        return ' '.join(translated_substrings), debug

    def _get_translations_substrings(self, level, words, source, target):
        length = len(words)
        debug = '\nTranslating sub strings, level=%s, words=%s' % (level, str(words))
        if length == 1 or length == level:
            translations = []
            for word in words:
                results = self._get_translations(word, source, target)
                if len(results):
                    translations.append(results[0]['value'])
                else:
                    translations.append(word)
            return translations, debug

        # The window size depends on the level
        window_size = length - level
        start = 0
        end = window_size
        # Move window from left to right, collect and translate sub strings
        translations = {}
        total_counts = {}
        i = 0
        found = False
        while end <= length:
            translations[i] = []
            total_counts[i] = 0
            substrings = []
            if start > 0:
                substrings.append(' '.join(words[0:start]))
            substrings.append(' '.join(words[start:end]))
            if end < length:
                substrings.append(' '.join(words[end:length]))
            # print substrings
            for substring in substrings:
                results = self._get_translations(substring, source, target)
                if len(results):
                    translations[i].append({'translation': results[0]['value'], 'count': results[0]['count'], 'string': substring})
                    total_counts[i] += results[0]['count']
                    found = True
                else:
                    translations[i].append({'translation': substring, 'count': 0, 'string': substring})
            debug += '\n' + str(translations[i])
            start += 1
            end += 1
            i += 1
        # If we didn't find any translation for the sub strings on this level, increase level => reduce substring size by one
        if not found:
            results, info = self._get_translations_substrings(level + 1, words, source, target)
            return results, debug + info
        # Found translations! Continue with the most promising substring translation, which is the one with the highest total count
        highest = (-1, 0)  # index, count
        for index, count in total_counts.iteritems():
            highest = (index, count) if count > highest[1] else highest
        # Try to translate any sub strings further where we didn't get a translation so far
        result = []
        for translation in translations[highest[0]]:
            if translation['count']:
                result.append(translation['translation'])
            else:
                sub, info = self._get_translations_substrings(1, translation['string'].split(), source, target)
                debug += info
                for word in sub:
                    result.append(word)
        return result, debug

    def _get_translations(self, string, source, target):
        # Lookup in cache
        results = self._get_cache(string, source, target)
        if len(results):
            return results
        # Search in Solr for an exact match of the string in the source language
        results = self._find_exact(string, source)
        if not results['numFound']:
            return []
        # Collect target translations, sorted by number of total counts
        candidates = {}
        for result in results['docs']:
            params = {
                'q': 'app_id:%s AND key:%s' % (result['app_id'], result['key'])
            }
            translations = self.solr.query(target, params)
            if not translations['numFound']:
                continue
            value = translations['docs'][0]['value'].lower()
            value = value.strip()
            candidates[value] = 1 if value not in candidates else candidates[value] + 1
        # Sort candidates by best translation candidate (having highest count)
        candidates = sorted(candidates.items(), key=operator.itemgetter(1), reverse=True)
        translations = []
        for candidate in candidates:
            translations.append({
                'value': candidate[0],
                'count': candidate[1]
            })
        self._store_cache(string, source, target, translations)
        return translations

    def _store_cache(self, string, source, target, translations):
        key = source + target
        if key not in self.cache:
            self.cache[key] = {}
        self.cache[key][string] = translations

    def _get_cache(self, string, source, target):
        key = source + target
        if key not in self.cache:
            return []
        if string in self.cache[key]:
            return self.cache[key][string]
        return []

    def _find_exact(self, string, lang):
        params = {
            'q': 'value_lc:"%s %s %s"' % (Solr.DELIMITER_START, string, Solr.DELIMITER_END),
            'rows': self.config['rows']
        }
        return self.solr.query(lang, params)


class TranslatorSolr(Translator):
    DEFAULT_CONFIG = {
        'rows': 100,  # Max. number of rows returned from search result
    }

    def __init__(self, url='http://localhost:8983', config={}):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)
        self.solr = Solr('', url)
        self.baseline = SolrBaselineSystem(self.solr, self.config)

    def get_id(self):
        return 'solr'

    def get_all(self, string, lang_from, lang_to):
        pass

    def translate_xml(self, xml, lang_from, lang_to):
        translations = []
        e = ExtractTranslationsFromXML(xml)
        strings = e.extract()
        debug = ''
        for key, string in strings.iteritems():
            translation, info = self.baseline.translate(utils.to_utf8(string), lang_from, lang_to)
            row = {
                'key': key,
                'source': string,
                'target': translation
            }
            translations.append(row)
            debug += '\n\n\n' + info if debug else info
        return {
            'debug': debug,
            'translations': translations
        }

    def get(self, strings, lang_from, lang_to):
        translations = []
        debug = ''
        for string in strings:
            translation, info = self.baseline.translate(utils.to_utf8(string), lang_from, lang_to)
            translations.append(translation)
            debug += '\n\n\n' + info if debug else info
        return {
            'debug': debug,
            'translations': translations
        }


class TranslatorCompare(Translator):
    def __init__(self, config={}, decoder_settings={}):
        self.config = config
        self.decoder_settings = decoder_settings
        self.solr = TranslatorSolr(config['solr_url'], decoder_settings['solr'])
        self.moses = TranslatorMoses(config['moses'], decoder_settings['moses'])
        self.tensorflow = TranslatorTensorflow(decoder_settings['tensorflow'])

    def get_all(self, string, lang_from, lang_to):
        pass

    def translate_xml(self, xml, lang_from, lang_to):
        translations = []
        e = ExtractTranslationsFromXML(xml)
        strings = e.extract()
        result_moses = self.moses.get(strings, lang_from, lang_to)
        result_solr = self.solr.get(strings, lang_from, lang_to)
        result_tensorflow = self.tensorflow.get(strings, lang_from, lang_to)
        i = 0
        for key, string in strings.iteritems():
            translations.append({
                'key': key,
                'source': string,
                'moses': result_moses['translations'][i],
                'tensorflow': result_tensorflow['translations'][i],
                'solr': result_solr['translations'][i],
            })
            i += 1
        return {
            'debug': '',
            'translations': translations
        }

    def get(self, strings, lang_from, lang_to):
        results_moses = self.moses.get(strings, lang_from, lang_to)
        results_tensorflow = self.tensorflow.get(strings, lang_from, lang_to)
        results_solr = self.solr.get(strings, lang_from, lang_to)
        translations = []
        for i, string in enumerate(strings):
            translations.append({
                'source': string,
                'moses': results_moses['translations'][i],
                'tensorflow': results_tensorflow['translations'][i],
                'solr': results_solr['translations'][i],
            })
        return {
            'debug': '',
            'translations': translations
        }


import getopt
import sys

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:t:s:', ['input=', 'target_lang=', 'source_lang='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    input = ''
    source_lang = 'en'
    target_lang = 'fr'
    for opt, arg in opts:
        if opt in ('-s', '--source_lang'):
            source_lang = arg
        if opt in ('-t', '--target_lang'):
            target_lang = arg
        if opt in ('-i', '--input'):
            input = arg

    trans = TranslatorSolr()
    if os.path.isfile(input):
        with open(input) as f:
            i = 0
            for string in f:
                result = trans.get([string.strip()], source_lang, target_lang)
                print utils.to_utf8(result['translations'][0])
                if i % 100 == 0:
                    sys.stderr.write('Translated %s strings so far...\n' % str(i))
                i += 1
    else:
        result = trans.get([input.strip()], source_lang, target_lang)
        print utils.to_utf8(result['translations'][0])
