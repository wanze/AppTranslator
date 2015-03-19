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


	"""
	folder: Absolute path to a folder where the extracted APK files are stored
	"""
	def __init__(self, folder):
		self.folder = folder
		self.counts = {'en' : 0}


	"""
	Execute script
	"""
	def execute(self):
		self.parseFolder(self.folder)
		print self.formatOutput(self.GLUE)


	"""
	Recursive parses the given folder until we hit the "res" folder containing the translations.
	"""
	def parseFolder(self, folder):
		files = os.listdir(folder)
		for f in files:
			file = os.path.realpath(os.path.join(folder, f)) # Build absolute path
			if f == 'res':
				# We are in the "res" folder, this folder contains a values folder per language
				self.countLanguagesOfFolder(file)
			elif os.path.isdir(file):
				# Not yet in the "res" folder, go recursive
				self.parseFolder(file)


	
	"""
	Count the languages from the given res folder (increment total count in dictionary)
	Note: For simplicity ATM, we assume that the folder "values" contains english strings; this may not be true
	"""
	def countLanguagesOfFolder(self, folder):
		folders = os.listdir(folder)
		self.counts['en'] += 1; 
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
		


	"""
	Return formated counts per language, separated with a delimiter
	"""
	def formatOutput(self, delimiter):
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

	if not os.path.isdir(folder):
		print folder + " is not a valid folder"
		sys.exit(2)

	counter = APKLanguageCounter(folder)
	counter.execute()

main()

