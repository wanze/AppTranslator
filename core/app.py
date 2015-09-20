import sys
import json
import urllib
from flask import Flask
from flask import request
from flask import Response
from database import SolrDatabase
from translator import Translator

app = Flask(__name__)
translator = Translator(SolrDatabase())

@app.after_request
def add_header(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/translate')
def get_translations():
    string = request.args.get('string')
    print string
    lang_from = request.args.get('from')
    lang_to = request.args.get('to')
    out = json.dumps(translator.get_all(string, lang_from, lang_to))
    return Response(out, mimetype='application/json')

if __name__ == '__main__':
    debug = '--debug' in sys.argv
    app.debug = debug
    app.run()
