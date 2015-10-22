import sys
import json
import urllib
import os
from flask import Flask
from flask import request
from flask import Response
from werkzeug import secure_filename
import translator

app = Flask(__name__)
trans = translator.TranslatorMoses('/home/vagrant/mosesdecoder')
app.config['UPLOAD_FOLDER'] = os.path.dirname(os.path.realpath(__file__)) + '/../data/temp/upload/'

@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/upload', methods=['POST'])
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

@app.route('/translateXML')
def translate_xml():
    lang_from = request.args.get('from')
    lang_to = request.args.get('to')
    xml_filename = request.args.get('xml_filename')
    xml_file = os.path.join(app.config['UPLOAD_FOLDER'], xml_filename)
    out = json.dumps(trans.translate_xml(xml_file, lang_from, lang_to))
    return Response(out, mimetype='application/json')


@app.route('/get')
def get_translations():
    string = request.args.get('string')
    lang_from = request.args.get('from')
    lang_to = request.args.get('to')
    out = json.dumps(trans.get(string, lang_from, lang_to))
    return Response(out, mimetype='application/json')

if __name__ == '__main__':
    debug = '--debug' in sys.argv
    app.debug = debug
    app.run(host='0.0.0.0')
