# AppTranslator

## Extract translations from APK files

```
$ ./extract_apk_translations.sh /var/apks/ /var/apks_extracted/
```

**Parameters**
* `1st` Absolute path to a folder containing the APK files
* `2nd` Absolute path to a folder where the extracted translations are stored

## Count languages over extracted APK files
```
$ python count_languages.py -f /var/apks_extracted/ > counts.csv
```

**Parameters**
* `-f` Absolute path to a folder where the extracted translations are stored
