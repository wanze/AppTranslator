class Translator(object):

    def __init__(self, database):
        self.database = database

    def get(self, string, lang_from, lang_to):
        # TODO
        pass

    def get_all(self, string, lang_from, lang_to):
        return self.database.get_translations(string, lang_from, lang_to)
