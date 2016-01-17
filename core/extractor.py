import os
import re
import xml.etree.ElementTree as ElementTree
from HTMLParser import HTMLParser
import shutil

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
            language = match.group(1) if match else 'en'
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
        self.error_fixing_attempt = 0

    def extract(self):
        if not os.path.isfile(self.xml_file) or self.error_fixing_attempt >= 10:
            return {}
        try:
            xml = ElementTree.parse(self.xml_file, parser=self.parser)
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
        except ElementTree.ParseError as e:
            # Try to clean the invalid line and re-parse :)
            line, _ = e.position
            if self.error_fixing_attempt == 0:
                # First error correction, save original XML file
                shutil.copyfile(self.xml_file, self.xml_file + '.orig')
            with open(self.xml_file, 'r') as input:
                with open(self.xml_file + '.new', 'w') as output:
                    l = 1
                    for translation in input:
                        if l != line:
                            output.write(translation)
                        l += 1
            os.rename(self.xml_file, self.xml_file + '.error')
            os.rename(self.xml_file + '.new', self.xml_file)
            e = ExtractTranslationsFromXML(self.xml_file)
            e.error_fixing_attempt = self.error_fixing_attempt + 1
            return e.extract()


class TranslationStringSanitizer(object):

    def __init__(self):
        self.html_stripper = HTMLTagsStripper()

    def sanitize(self, value):
        value = value.strip()
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
        # Replace placeholders in form of '%s' or '%1$s'
        value = re.sub('%s|%d|(s|d)?%[0-9]+\$(s|d)?', '', value)
        if len(value) < 3:
            return ''
        if not re.search('\w', value):
            return ''
        return value.strip()

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
