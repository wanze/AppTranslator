import urllib
import urllib2
import json


class Database(object):
    def get_translations(self, string, lang_from, lang_to, options={}):
        """
        string     -- The string to translate
        lang_from  -- Source language, e.g. 'en', 'de'
        lang_to    -- Target language, e.g. 'fr', 'ru'
        options    -- Dictionary with options specific to the database

        Returns a dictionary
        {
            'translations' : <Array of matched translation strings>,
            'debug' : <Dictionary with additional debug information>
        }
        """
        raise NotImplementedError('Must be implemented by subclass')


class SolrDatabase(Database):
    def __init__(self, url='http://localhost:8983'):
        self.url = url

    def get_translations(self, string, lang_from, lang_to, options={}):
        response1 = self._query(string, lang_from)
        # Extract all translation keys from the response dictionary
        keys = self._extract_translation_keys(response1)
        # Perform search in target language based on keys
        translations = []
        for key in keys:
            response = self._query('key:%s' % key, lang_to)
            if int(response['response']['numFound']) > 0:
                results = [doc['value'][0] for doc in response['response']['docs']]
                translations.extend(results)
        translations = set(translations)
        return {
            'debug': response1,
            'translations': list(translations)
        }

    def _query(self, string, lang):
        """
        Query Solr for the given string and language
        """
        query = {'q': string}
        url = self.url + '/solr/' + lang + '/select?' + urllib.urlencode(query) + '&wt=json'
        response = urllib2.urlopen(url)
        return json.loads(response.read())

    @staticmethod
    def _extract_translation_keys(response):
        """
        Parses a json response object from Solr and returns the translation keys of all strings found
        """
        return set([doc['key'][0] for doc in response['response']['docs']])
