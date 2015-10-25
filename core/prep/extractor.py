import os
import re
import xml.etree.ElementTree as ElementTree
import getopt
import sys

class Extractor(object):

    def __init__(self, folder_apk):
        self.folder_apk = folder_apk
        self.translations = {}

    def extract_app_id(self):
        file_manifest = os.path.join(self.folder_apk, 'AndroidManifest.xml')
        if not os.path.isfile(file_manifest):
            return ''
        xml = ElementTree.parse(file_manifest)
        app_id = xml.getroot().attrib['package']
        return app_id

    def extract_translations(self):
        folder_res = os.path.realpath(os.path.join(self.folder_apk, 'res'))  # Build absolute path
        for folder_value in os.listdir(folder_res):
            if folder_value[0] == '.':
                continue
            match = re.search('^values-(\w{2})$', folder_value)  # Extract the language
            language = match.group(1) if match else 'en'  # TODO: This is an assumption currently, we need to check if the content is english!
            folder_trans = os.path.realpath(os.path.join(folder_res, folder_value))
            self.translations[language] = self.get_translations(os.path.join(folder_trans, 'strings.xml'))
        return self.translations

    @staticmethod
    def get_translations(xml_file):
        if not os.path.isfile(xml_file):
            return
        xml = ElementTree.parse(xml_file)
        translations = {}
        for trans in xml.getroot():
            key = trans.attrib['name']
            if not trans.text:
                continue
            value = Extractor.sanitize_translation_string(trans.text.encode('utf-8'))  # Clean/remove unwanted strings
            translations[key] = value
        return translations

    @staticmethod
    def sanitize_translation_string(value):
        """
        Sanitize translation string
        """
        value = value.strip()
        for replacement in ['\n', '\r', '\t', '"']:
            value = value.replace(replacement, '')
        for string in ['http', 'www']:
            if value.startswith(string):
                return ''
        return value
