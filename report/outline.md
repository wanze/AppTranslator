# Introduction
Basic introduction to the problem of machine translation, advent of the mobile apps, untapped translation resources, and the current idea of utilizing them for targeted translations for mobile apps (the story).

# PROBLEM: 

## Automatic translation of android apps
Describe the problem in detail

## Android apps and internationalization
Overview how i18n is handled in android apps.

# SOLUTION

## Data collection: Collect apps and extract translations
How to extract and preprocess translations from APK files.
Some statistics here on how much data was collected in different dimentions (number of apps, translations, languages, etc.)
(top terms?)

## Data storage and access (Solr)
Some words about the storage engine and the strategy how we stored translations.

## Statistical Machine translation
Short introduction to statistical MT

### Phrase-based machine translation
How phrase-based MT works --> Moses

### Deep learning
How MT with neural networks works --> Lamtram, TensorFlow

## The application
Describe how the developed application (frontend & backend) works.

### Backend
Describe architecture and implemented decoders. TODO: One sub-chapter per decoder? (what is a decoder - let's discuss)

### Frontend
Describe Frontend for the app with AngularJS

# PART III: EVALUATION

## Comparing results of the different decoders
What kind of translations work well on which decoder?

## BLEU score
How BLEU works, how we did measure BLEU with cross validation, show results of different decoders.

## Comparison to google translate
Idea: Translate a popular app that is not part of the training/testing data. Compare our results with the translation
output of google translate

## Feedback of app developers
Ask people if they would use a service to auto-translate their apps.

# RELATED WORK

Find some related work? :)

# CONCLUSION AND FUTURE WORK

## Future work
* Store more metadata for apps. Use this data in the decoding process to rate a translation candidate, e.g. n downloads, rating, category etc.
* Combine multiple decoders or choose the optimal decoder based on input
* Translation service: Improve translation quality with crowdsourcing

## Conclusion
