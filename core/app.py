import sys
import json
import urllib
import os
from flask import Flask
from flask import request
from flask import Response
from werkzeug import secure_filename
import translator


class AppTranslator:

    DEFAULT_CONFIG = {
        'debug': False,
        'port': 5000,
        'moses': '/home/vagrant/mosesdecoder'
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
            return response

        @self.app.route('/upload', methods=['POST'])
        def upload():
            # TODO Move to class
            f = request.files['file']
            if f and f.filename.rsplit('.', 1)[1] == 'xml':
                filename = secure_filename(f.filename)
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                out = json.dumps({'success': True, 'filename': filename})
            else:
                out = json.dumps({'success': False})
            return Response(out, mimetype='application/json')

        @self.app.route('/translateXML')
        def translate_xml():
            trans = translator.TranslatorMoses(self.config['moses'])
            lang_from = request.args.get('from')
            lang_to = request.args.get('to')
            xml_filename = request.args.get('xml_filename')
            xml_file = os.path.join(self.app.config['UPLOAD_FOLDER'], xml_filename)
            out = json.dumps(trans.translate_xml(xml_file, lang_from, lang_to))
            return Response(out, mimetype='application/json')


        @self.app.route('/get')
        def get_translation():
            trans = translator.TranslatorMoses(self.config['moses'])
            string = request.args.get('string')
            lang_from = request.args.get('from')
            lang_to = request.args.get('to')
            out = json.dumps(trans.get(string, lang_from, lang_to))
            return Response(out, mimetype='application/json')

    def run(self):
        self.app.run(host='0.0.0.0', port=self.config['port'], debug=self.config['debug'])


if __name__ == '__main__':
    debug = '--debug' in sys.argv
    config_file = open(os.path.dirname(os.path.realpath(__file__)) + '/../config/app.json')
    config = json.loads(config_file.read())
    app = AppTranslator(config)
    app.run()