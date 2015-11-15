import sys
import os
import hashlib
import json
from flask import Flask
from flask import request
from flask import Response
import translator


class AppTranslator:

    DEFAULT_CONFIG = {
        'debug': False,
        'port': 5000,
        'moses': '/home/vagrant/mosesdecoder',
        'lamtram': '/home/vagrant/lamtram',
        'solr': '/home/vagrant/solr'
    }

    def __init__(self, config):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config.update(config)
        self.app = Flask(__name__)
        self.init()
        self.init_routes()

    def init(self):
        upload_folder = os.path.dirname(os.path.realpath(__file__)) + '/../data/temp/upload/'
        if not os.path.isdir(upload_folder):
            os.makedirs(upload_folder)
        self.app.config['UPLOAD_FOLDER'] = upload_folder

    def init_routes(self):
        @self.app.after_request
        def add_header(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Origin, X-Requested-With, Content-Type, Accept'
            return response

        @self.app.route('/upload', methods=['POST'])
        def upload():
            # TODO Move to class
            f = request.files['file']
            if f and f.filename.rsplit('.', 1)[1] == 'xml':
                filename = hashlib.md5(f.filename).hexdigest()
                f.save(os.path.join(self.app.config['UPLOAD_FOLDER'], filename))
                out = json.dumps({'success': True, 'filename': filename})
            else:
                out = json.dumps({'success': False})
            return Response(out, mimetype='application/json')

        @self.app.route('/translateXML', methods=['POST'])
        def translate_xml():
            data = json.loads(request.data)
            trans = self._get_decoder(data['decoder'], data['decoder_settings'])
            xml_file = os.path.join(self.app.config['UPLOAD_FOLDER'], data['xml_filename'])
            out = json.dumps(trans.translate_xml(xml_file, data['lang_from'], data['lang_to']))
            return Response(out, mimetype='application/json')

        @self.app.route('/translateStrings', methods=['POST'])
        def get_translation():
            data = json.loads(request.data)
            trans = self._get_decoder(data['decoder'], data['decoder_settings'])
            print data['strings']
            out = json.dumps(trans.get(data['strings'], data['lang_from'], data['lang_to']))
            return Response(out, mimetype='application/json')

    def _get_decoder(self, type, settings):
        if type == 'moses':
            return translator.TranslatorMoses(self.config['moses'], settings)
        elif type == 'lamtram':
            return translator.TranslatorLamtram(self.config['lamtram'])

    def run(self):
        self.app.run(host='0.0.0.0', port=self.config['port'], debug=self.config['debug'])


if __name__ == '__main__':
    debug = '--debug' in sys.argv
    config_file = open(os.path.dirname(os.path.realpath(__file__)) + '/../config/app.json')
    config = json.loads(config_file.read())
    app = AppTranslator(config)
    app.run()
