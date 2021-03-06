import os
import xml.etree.ElementTree as ElementTree
import urllib2
import urllib
import subprocess
import json
import operator
import utils

class Solr:

    SOLR_DATA_DIR = os.path.join('solr', 'data')
    CONFIGSET_TRANSLATIONS = 'translations'
    CONFIGSET_APPS = 'apps'
    DELIMITER_START = 'SOLR_S'
    DELIMITER_END = 'SOLR_E'

    def __init__(self, dir_solr='', solr_url=''):
        """
        dir_solr -- Absolute path to Solr
        solr_url -- URL to Solr
        """
        self.dir_solr = dir_solr.rstrip(os.sep) + os.sep
        self.solr_url = solr_url.rstrip('/') if solr_url else 'http://localhost:8983'
        # The instance directory storing the index for the different cores
        self.dir_data = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../config')), self.SOLR_DATA_DIR) + os.sep
        if not os.path.isdir(self.dir_data):
            os.makedirs(self.dir_data)
        self.cache_cores = self.get_cores()


    def get_cores(self):
        """
        Return a list of active cores, e.g. ['en', 'de', 'fr']
        """
        xml_response = self._call_solr_core_api({'action': 'STATUS'})
        xml = ElementTree.parse(xml_response)
        return [core.attrib['name'] for core in xml.getroot()[2]]


    def create_core(self, name, configset):
        """
        Create a new core in Solr with the given name, based on a configSet providing the solrconfig.xml and schema.xml files
        :param name: Name of the core
        :param configset: Name of configset
        """
        if self.exists_core(name):
            return

        params = {
            'action': 'CREATE',
            'name': name,
            'instanceDir': self.dir_data + name,
            'configSet': configset,
        }

        xml_response = self._call_solr_core_api(params)
        # Check XML response for errors, a status=0 indicates that the core was created successfully
        xml = ElementTree.parse(xml_response)
        status = int(xml.getroot()[0][0].text)
        if status == 0:
            self.cache_cores.append(name)
        else:
            raise Exception(xml.getroot()[1][0].text)  # TODO Check available errors, no docs available?


    def index(self, document, core, configset=''):
        """
        Index a Solr xml document (or path containing xml documents) into the given core
        """
        configset = self.CONFIGSET_TRANSLATIONS if not configset else configset
        if not self.exists_core(core):
            self.create_core(core, configset)
        cmd = self.dir_solr + os.path.join('bin', 'post')
        result = subprocess.call([cmd, '-c', core, document])
        return result


    def exists_core(self, name):
        return name in self.cache_cores


    def get_top_terms(self, core, n=10):
        """
        Returns the n top terms for the given core
        """
        if not self.exists_core(core):
            raise Exception("Core '" + core + "' does not exist")
        req = self._call_solr_api(core + '/terms', {'terms.fl': 'value', 'terms.limit': n})
        json_response = json.load(req)
        i = 0
        terms = []
        term = {}
        for value in json_response['terms']['value']:
            if i % 2 == 0:
                term['value'] = value.encode('utf-8')
            else:
                term['count'] = value
                terms.append(term)
                term = {}
            i += 1
        return terms

    def get_term_variations(self, lang_from, lang_to, term, max_rows=100):
        term = utils.to_utf8(term.lower())
        params = {
            'q': 'value_lc:"%s %s %s"' % (self.DELIMITER_START, term, self.DELIMITER_END),
            'rows': max_rows
        }
        results = self.query(lang_from, params)
        counts = {}
        for result in results['docs']:
            params = {
                'q': 'app_id:%s AND key:%s' % (result['app_id'], result['key'])
            }
            translation = self.query(lang_to, params)
            if translation['numFound']:
                value = translation['docs'][0]['value'].lower()
                value = value.strip()
                counts[value] = 1 if value not in counts else counts[value] + 1
        # Sort dict by counts
        counts_sorted = sorted(counts.items(), key=operator.itemgetter(1), reverse=True)
        variations = []
        for item in counts_sorted:
            variations.append({
                'term': item[0],
                'count': item[1]
            })
        return variations

    def query(self, core, query_params):
        try:
            results = json.load(self._call_solr_api(core + '/select', query_params))
            results['response']['error'] = False
            return results['response']
        except urllib2.HTTPError as e:
            return {
                'numFound': 0,
                'docs': [],
                'error': e.strerror
            }


    def _call_solr_api(self, endpoint, params):
        """
        endpoint -- Must contain request handler and core, e.g. select/en or terms/en
        params   -- Dictionary of additional params to send
        """
        params['wt'] = 'json'
        # print self.solr_url + '/solr/' + endpoint + '?' + urllib.urlencode(params)
        return urllib2.urlopen(self.solr_url + '/solr/' + endpoint + '?' + urllib.urlencode(params))


    def _call_solr_core_api(self, params):
        # print self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params)
        return urllib2.urlopen(self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params))
