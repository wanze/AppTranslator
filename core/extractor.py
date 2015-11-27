import os
import re
import xml.etree.ElementTree as ElementTree
from HTMLParser import HTMLParser
import cgi


class Extractor(object):

    def __init__(self, folder_apk):
        self.folder_apk = folder_apk
        self.translations = {}

    def extract_app_id(self):
        file_manifest = os.path.join(self.folder_apk, 'AndroidManifest.xml')
        if not os.path.isfile(file_manifest):
            return ''
        try:
            xml = ElementTree.parse(file_manifest)
        except ElementTree.ParseError:
            return ''
        app_id = xml.getroot().attrib['package']
        return app_id

    def extract_translations(self):
        folder_res = os.path.realpath(os.path.join(self.folder_apk, 'res'))
        if not os.path.isdir(folder_res):
            return self.translations
        for folder_value in os.listdir(folder_res):
            if folder_value[0] == '.':
                continue
            match = re.search('^values-(\w{2})$', folder_value)
            language = match.group(1) if match else 'en'  # TODO: This is an assumption currently, we need to check if the default language is english!
            folder_trans = os.path.realpath(os.path.join(folder_res, folder_value))
            self.translations[language] = self.get_translations(os.path.join(folder_trans, 'strings.xml'))
        return self.translations

    @staticmethod
    def get_translations(xml_file):
        e = ExtractTranslationsFromXML(xml_file)
        return e.extract()


class ExtractTranslationsFromXML(object):

    def __init__(self, xml_file):
        self.xml_file = xml_file
        self.sanitizer = TranslationStringSanitizer()
        self.parser = ElementTree.XMLParser(encoding='utf-8')

    def extract(self):
        if not os.path.isfile(self.xml_file):
            return {}
        try:
            xml = ElementTree.parse(self.xml_file, parser=self.parser)
        except ElementTree.ParseError:
            return {}
        translations = {}
        for trans in xml.getroot():
            key = trans.attrib['name']
            if not trans.text:
                continue
            value = self.sanitizer.sanitize(trans.text.encode('utf-8'))  # Clean/remove unwanted strings
            if not value:
                continue
            translations[key] = value
        return translations


class TranslationStringSanitizer(object):

    PLACEHOLDER_TOKEN = 'STRING-PLACEHOLDER-TOKEN'

    def __init__(self):
        self.html_stripper = HTMLTagsStripper()

    def sanitize(self, value):
        value = value.strip()
        if len(value) <= 3:
            return ''
        # Ignore numbers and floats
        if self.is_number(value):
            return ''
        # Replace special chars
        for replacement in ['\n', '\r', '\t', '"']:
            value = value.replace(replacement, '')
        # Ignore URLs
        for string in ['http', 'www']:
            if value.startswith(string):
                return ''
        # Strip any HTML tags
        s = HTMLTagsStripper()
        s.feed(value)
        value = s.get_data()
        # Replace %s and %1$s with a placeholder token
        value = re.sub(r"%(s|[0-9]+\$s)", self.PLACEHOLDER_TOKEN, value)
        # Encode special chars
        value = cgi.escape(value)
        return value

    @staticmethod
    def is_number(string):
        try:
            float(string)
            return True
        except ValueError:
            return False


class HTMLTagsStripper(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.reset()
        self.fed = []

    def error(self, message):
        pass

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)
