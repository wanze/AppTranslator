import os
import re
import getopt
import sys
import xml.etree.ElementTree as ElementTree
import urllib2
import urllib
import subprocess
import zipfile
import extractor
import time

"""
Preprocess extracted translations and index them into Solr

Usage: 
$ python translations2solr.py --input_dir=/path/to/extracted/APKs --solr_dir=/path/to/solr --output_dir=/path/to/output_dir

Arguments:
--input_dir			Path to a zip file or folder containing APK files
--output_dir        Path to a directory where the Solr XML files are written
--mode              (EI|E|I) where 'E' does extract/preprocess translations as Solr XML; 'I' does index them into Solr (default='EI', meaning extract AND index)
--solr_dir  		Path to Solr directory. Note: Mandatory for mode 'I'
--solr_url  		URL to access Solr (default='http://localhost:8983') Note: Mandatory for mode 'I'

@author Stefan Wanzenried <stefan.wanzenried@gmail.com>
"""


class Solr:

    SOLR_DATA_DIR = os.path.join('solr', 'data')
    SOLR_CONFIGSET = 'transapp'

    def __init__(self, dir_solr, solr_url=''):
        """
        dir_solr -- Absolute path to Solr
        solr_url -- URL to Solr
        """
        self.dir_solr = dir_solr.rstrip(os.sep) + os.sep
        self.solr_url = solr_url.rstrip('/') if solr_url else 'http://localhost:8983'
        # The instance directory storing the index for the different cores
        self.dir_data = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../config')), self.SOLR_DATA_DIR) + os.sep
        if not os.path.isdir(self.dir_data):
            os.makedirs(self.dir_data)
        self.cache_cores = self.get_cores()


    def get_cores(self):
        """
        Return a list of active cores, e.g. ['en', 'de', 'fr']
        """
        xml_response = self._call_solr_api({'action': 'STATUS'})
        xml = ElementTree.parse(xml_response)
        return [core.attrib['name'] for core in xml.getroot()[2]]


    def create_core(self, name):
        """
        Create a new core in Solr with the given name, based on a configSet providing the solrconfig.xml and schema.xml files
        """
        if self.exists_core(name):
            return

        params = {
            'action': 'CREATE',
            'name': name,
            'instanceDir': self.dir_data + name,
            'configSet': self.SOLR_CONFIGSET,
        }

        xml_response = self._call_solr_api(params)
        # Check XML response for errors, a status=0 indicates that the core was created successfully
        xml = ElementTree.parse(xml_response)
        status = int(xml.getroot()[0][0].text)
        if status == 0:
            self.cache_cores.append(name)
        else:
            raise Exception(xml.getroot()[1][0].text)  # TODO Check available errors, no docs available?


    def index(self, document, core):
        """
        Index a Solr xml document (or path containing xml documents) into the given core
        """
        print "Start indexing '" + document + "' into core " + core + "\n"
        if not self.exists_core(core):
            self.create_core(core)
        cmd = self.dir_solr + os.path.join('bin', 'post')
        print subprocess.call([cmd, '-c', core, document])
        time.sleep(10)

    def exists_core(self, name):
        return name in self.cache_cores


    def _call_solr_api(self, params):
        # print self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params)
        return urllib2.urlopen(self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params))


class Translations2Solr:

    # Contains extracted translations and preprocessed solr xml files
    TMP_DIR_SOLR_XML = 'solr_xml'

    def __init__(self, dir_apks_in, dir_xml_out, solr):
        """
        dir_apks_in -- Absolute path of directory containing extracted APK files, one folder per app
        dir_xml_out -- Absolute path to directory where the Solr XML files are written
        solr        -- Instance of class Solr
        """
        self.dir_apks_in = dir_apks_in.rstrip('/') + '/'
        self.dir_xml_out = dir_xml_out.rstrip('/') + '/'
        if not os.path.isdir(self.dir_xml_out):
            os.makedirs(self.dir_xml_out)
        self.solr = solr


    def write_xml(self):
        """
        Create solr xml files of extracted translations
        """
        print self.dir_apks_in
        for f in os.listdir(self.dir_apks_in):
            if f[0] == '.':
                continue
            apk_folder = os.path.realpath(os.path.join(self.dir_apks_in, f))
            ext = extractor.Extractor(apk_folder)
            app_id = ext.extract_app_id()
            print "\nPrepare solr xml for app: " + app_id + "\n"
            translations = ext.extract_translations()
            for language in translations:
                self._create_solr_xml_file(app_id, language, translations[language])


    def index(self):
        """
        Index solr xml files into Solr
        """
        for language in os.listdir(self.dir_xml_out):
            if language == '.':
                continue
            dir_xml_docs = os.path.join(self.dir_xml_out, language)
            self.solr.index(dir_xml_docs, language)


    def _create_solr_xml_file(self, app_id, language, translations):
        """
        Write an xml file
        """
        if not translations:
            return
        dir_xml = os.path.join(self.dir_xml_out, language)
        if not os.path.isdir(dir_xml):
            os.makedirs(dir_xml)
        temp_filename = os.path.join(dir_xml, app_id + '.xml.tmp')
        file_temp = open(temp_filename, 'w+')
        file_temp.write('<add>\n')
        for key, value in translations.iteritems():
            if not value:
                continue
            file_temp.write('<doc>\n')
            file_temp.write('<field name="id">' + '_'.join([app_id, key]) + '</field>\n')
            file_temp.write('<field name="app_id">' + app_id + '</field>\n')
            file_temp.write('<field name="key">' + key + '</field>\n')
            file_temp.write('<field name="value">' + value + '</field>\n')
            file_temp.write('</doc>\n')
        file_temp.write('</add>\n')
        file_temp.close()
        file_xml = temp_filename.replace('.xml.tmp', '.xml')
        os.rename(temp_filename, file_xml)
        return file_xml


if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:m:d:u:o:', ['input_dir=', 'mode=', 'solr_dir=', 'solr_url=', 'output_dir='])
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(2)

    input_dir = ''
    mode = 'EI'  # EXTRACT && INDEX
    solr_dir = ''
    solr_url = ''
    output_dir = ''
    for opt, arg in opts:
        if opt in ('-i', '--input_dir'):
            input_dir = arg
        if opt in ('-m', '--mode'):
            mode = arg
        if opt in ('-d', '--solr_dir'):
            solr_dir = arg
        if opt in ('-u', '--solr_url'):
            solr_url = arg
        if opt in ('-o', '--output_dir'):
            output_dir = arg

    print output_dir
    print mode
    # mode = extract
    if 'e' in mode.lower():
        if not os.path.isdir(input_dir):
            print input_dir + " must be a folder containing extracted APK files"
            sys.exit(2)

    # mode = index
    solr = None
    if 'i' in mode.lower():
        if not os.path.isdir(solr_dir):
            print "The path to Solr '" + solr_dir + "' is not valid"
            sys.exit(2)
        else:
            solr = Solr(solr_dir, solr_url)

    # Run it!
    app = Translations2Solr(input_dir, output_dir, solr)
    if 'e' in mode.lower():
        app.write_xml()
    if 'i' in mode.lower():
        app.index()
