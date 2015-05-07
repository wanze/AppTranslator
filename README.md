# AppTranslator

## Installation

1. Download and extract the latest version of Solr from the [Apache Solr Website](http://lucene.apache.org/solr/)
2. Clone this repository: `git clone https://github.com/wanze/AppTranslator.git`
3. Navigate to the extracted Solr directory and open the file `server/solr/solr.xml`. Add the following line somewhere below the `<solr>` root element: 
```
<configSetBaseDir>path/to/this/repoisotry/AppTranslator/solr/configsets</configSetBaseDir>
```

## Usage

Start Solr by executing `bin/solr start` in the root directory of Solr.

### Extract and Index translations into Solr
Use the python script `translations2solr.py` to extract / process and index translations into Solr.

```
$ cd import
$ python translations2solr.py --input=/path/to/APKs.zip --solr_dir=/path/to/solr/directory
```

**Parameters**
* `--input` Absolute path to a .zip file or folder containing .apk files. If a zip file is provided, the apk files are extracted first.
* `--mode` (EI|E|I) where 'E' does extract/preprocess translations and store them temporary; 'I' does index them into Solr (default='EI', meaning extract first AND index afterwards)
* `--solr_dir` Path to Solr directory, mandatory for mode 'I'
* `--solr_url` URL to access Solr (default='http://localhost:8983') Note: Mandatory for mode 'I'

Note: The script stores temporary data (e.g. the Solr xml files containing the translations) in the directory `import/translations2solr`. This folder is excluded from this repository.
