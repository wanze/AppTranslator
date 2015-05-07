#!/usr/bin/env bash

# This script extracts APK files from a folder with the apktool.jar library. 
# Other folders/files than the translations are deleted in order to save disk space ;) 
# 
# 1st parameter: Absolute path to the folder containing the APK files
# 2nd parameter: Absolute path to a folder where the extracted files are written, one folder per APK is generated
# 
# Note: The apktool.jar file must be within the same folder as this script
# 
# Example:
# ./extract_apk_translations /var/apks/ /var/apks_extracted/
# 

dir_in=$1
dir_out=$2
dir_current=$PWD

# Normalize input directory, add trailing slash if necessary
if [[ $dir_in =~ \/$ ]]; then
	dir_in="${dir_in}*"
else
	dir_in="${dir_in}/*"
fi

# Loop APK files
for file in $dir_in; do
	name=$(basename "$file")
	echo "Extracting $name...."
	dir_target="${dir_out}/${name}"

	# Run APK Tool for the current APK file
	java -jar apktool.jar d "$file" -o "$dir_target" -s
	
	# Remove assets and other folders/files not interested in
	cd "$dir_target"
	rm -R assets
	rm -R original
	rm -R lib
	rm -R unknown
	rm classes.dex

	# Go into res folder and delete everything but translations
	cd res
	for resource in *; do
		if ! [[ $resource =~ ^values\-?[a-z]{0,2}$ ]]; then
			# This is not a valid translation values folder, e.g. "values", "values-de", "values-fr"
			rm -R "$resource"
		fi
	done
	cd "$dir_current"
done


