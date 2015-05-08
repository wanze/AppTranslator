import os
import re
import getopt
import sys
import xml.etree.ElementTree as ElementTree
import urllib2
import urllib
import subprocess
import zipfile

"""
Preprocess extracted translations and index them into Solr

Usage: 
$ python translations2solr.py --input=/path/to/APKs.zip --solr_dir=/path/to/solr

Arguments:
--input			Path to a zip file or folder containing APK files
--mode			(EI|E|I) where 'E' does extract/preprocess translations and store them temporary; 'I' does index them into Solr (default='EI', meaning extract AND index)
--solr_dir		Path to Solr directory. Note: Mandatory for mode 'I'
--solr_url		URL to access Solr (default='http://localhost:8983') Note: Mandatory for mode 'I'

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
		self.dir_data = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), self.SOLR_DATA_DIR) + os.sep
		self.cache_cores = self.getCores()
	

	def getCores(self):
		"""
		Return a list of active cores, e.g. ['en', 'de', 'fr']
		"""
		xml_response = self._callSolrAPI({'action' : 'STATUS'})
		xml = ElementTree.parse(xml_response)
		return [core.attrib['name'] for core in xml.getroot()[2]]


	def createCore(self, name):
		"""
		Create a new core in Solr with the given name, based on a configSet providing the solrconfig.xml and schema.xml files
		"""
		if self.existsCore(name):
			return
		
		params = {
			'action' : 'CREATE',
			'name' : name,
			'instanceDir' : self.dir_data + name,
			'configSet' : self.SOLR_CONFIGSET,
		}
	
		xml_response = self._callSolrAPI(params)
		# Check XML response for errors, a status=0 indicates that the core was created successfully
		xml = ElementTree.parse(xml_response)
		status = int(xml.getroot()[0][0].text)
		if status == 0:
			self.cache_cores.append(name)
		else:
			raise Exception(xml.getroot()[1][0].text) # TODO Check available errors, no docs available?


	def index(self, document, core):
		"""
		Index a Solr xml document (or path containing xml documents) into the given core
		"""
		print "Start indexing '" + document + "' into core " + core + "\n"
		if not self.existsCore(core): self.createCore(core)
		cmd = self.dir_solr + os.path.join('bin', 'post')
		print subprocess.call([cmd, '-c', core, document])


	def existsCore(self, name):
		return name in self.cache_cores


	def _callSolrAPI(self, params):
		# print self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params)
		return urllib2.urlopen(self.solr_url + '/solr/admin/cores?' + urllib.urlencode(params))



class Translations2Solr:

	# Contains extracted translations and preprocessed solr xml files
	TMP_DIR = 'translations2solr'
	TMP_DIR_EXTRACTED = 'extracted_languages'
	TMP_DIR_SOLR_XML = 'solr_xml'


	def __init__(self, dir_apks_in, solr):
		"""
		dir_apks_in -- Absolute path of directory containing extracted APK files, one folder per app
		solr        -- Instance of class Solr
		"""
		self.dir_current = os.path.dirname(os.path.abspath(__file__))
		self.dir_apks_in = dir_apks_in
		self.dir_temp = os.path.join(self.dir_current, self.TMP_DIR)
		self.dir_temp_extracted = os.path.join(self.dir_temp, self.TMP_DIR_EXTRACTED)
		self.dir_temp_solr_xml = os.path.join(self.dir_temp, self.TMP_DIR_SOLR_XML)
		self.solr = solr


	def extract_translations(self):
		"""
		Extract all translations from the APK files and convert them to a solr xml file
		"""
		cmd = './extract_apk_translations.sh'
		print subprocess.call([cmd, self.dir_apks_in, self.dir_temp_extracted])
		self._prepare_solr_xml()


	def index(self):
		"""
		Index solr xml files into Solr
		"""
		for language in os.listdir(self.dir_temp_solr_xml):
			if language == '.': continue
			dir_xml_docs = os.path.join(self.dir_temp_solr_xml, language)			
			self.solr.index(dir_xml_docs, language)


	def _prepare_solr_xml(self):
		"""
		Create solr xml files of extracted translations
		"""
		for f in os.listdir(self.dir_temp_extracted):
			if f[0] == '.': continue
			apk_folder = os.path.realpath(os.path.join(self.dir_temp_extracted, f))
			file_manifest = os.path.join(apk_folder, 'AndroidManifest.xml')
			if not os.path.isfile(file_manifest): continue
			app_id = self._extractAppId(file_manifest)
			print "\nPrepare solr xml for app: " + app_id + "\n"
			# Loop folders inside 'res' folder, they contain the translations in different languages
			dir_values = os.path.join(apk_folder, 'res')
			for dir_value in os.listdir(dir_values):
				if dir_value[0] == '.': continue
				# Extract the language
				match = re.search('^values-(\w{2})$', dir_value)
				language = match.group(1) if match else 'en' # TODO: This is an assumption currently, we need to check if the content is english!	
				dir_trans = os.path.realpath(os.path.join(dir_values, dir_value))
				self._createSolrXMLFile(app_id, language, os.path.join(dir_trans, 'strings.xml'))


	def _createSolrXMLFile(self, app_id, language, file_translations):
		"""
		Convert a android translations xml file to a solr xml file 
		"""
		if not os.path.isfile(file_translations): return
		dir_xml = os.path.join(self.dir_temp_solr_xml, language)
		if not os.path.isdir(dir_xml): os.makedirs(dir_xml)
		temp_filename = os.path.join(dir_xml, app_id + '.xml.tmp')
		file_temp = open(temp_filename, 'w+')
		file_temp.write('<add>\n');
		xml = ElementTree.parse(file_translations)
		for trans in xml.getroot():
			key = trans.attrib['name']
			# Do not index empty translations...
			if not trans.text: continue
			value = trans.text.encode('utf-8')
			# Clean/remove unwanted strings
			value = self._sanitizeTranslationString(value) 
			if not value: continue
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


	def _sanitizeTranslationString(self, value):
		"""
		Remove uninteresting translations (e.g. links, HTML)
		"""
		for str in ['http', 'www']:
			if value.startswith(str): return ''
		return value

	def _extractAppId(self, file_manifest):
		"""
		Return the unique app ID from a given android manifest xml file
		"""
		xml = ElementTree.parse(file_manifest)
		app_id = xml.getroot().attrib['package']
		return app_id


def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'i:m:d:u:', ['input=', 'mode=', 'solr_dir=', 'solr_url='])
	except getopt.GetoptError as err:
		print str(err)
		sys.exit(2)

	_input = ''
	mode = 'EI' # EXTRACT && INDEX
	solr_path = ''
	solr_url = ''
	for opt, arg in opts:
		if opt in ('-i', '--input'):
			_input = arg
		if opt in ('-m', '--mode'):
			mode = arg
		if opt in ('-d', '--solr_dir'):
			solr_path = arg
		if opt in ('-u', '--solr_url'):
			solr_url = arg

	# mode = extract
	if 'e' in mode.lower():
		if not os.path.isfile(_input) and not os.path.isdir(_input):
			print _input + " must be a folder or .zip file containing APK files"
			sys.exit(2)

		# _input supports ZIP file or directory containing APKs. In case of a zip, extract it first
		if _input.endswith('.zip'):
			dir_extract = os.path.join(os.path.dirname(os.path.abspath(_input)),os.path.basename(_input).rstrip('.zip'))
			print "Extracting content of '" + _input + "' to '" + dir_extract + "'..." 
			with zipfile.ZipFile(_input, 'r') as z:
				z.extractall(dir_extract)
			_input = dir_extract

	# mode = index
	solr = None
	if 'i' in mode.lower():
		if not os.path.isdir(solr_path):
			print "The path to Solr '" + solr_path + "' is not valid"
			sys.exit(2)
		else:
			solr = Solr(solr_path, solr_url)
	
	# Run it!
	app = Translations2Solr(_input, solr)
	if 'e' in mode.lower():
		app.extract_translations()
	if 'i' in mode.lower():
		app.index()

main()

