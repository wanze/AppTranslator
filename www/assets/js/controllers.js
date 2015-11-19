/**
 * Global App controller
 */
app.controller('AppController', function ($scope, $location) {

    $scope.app = {
        state: 'decode'
    };

    $scope.changeState = function (state) {
        $scope.app.state = state;
        $location.path('/' + state);
    };

});

/**
 * Controller for /decode
 */
app.controller('DecoderController', function ($scope, $http, Upload, $timeout, $sce, config) {

    $scope.state = {
        isLoading: false,
        loaded: false,
        progress: 0
    };

    $scope.decoder = {
        decoder: 'moses',
        moses: {
            drop_unknown: '0',
            search_algorithm: 0,
            max_phrase_length: 20,
            verbose: 2,
            stack: 100,
            tune_weights: 0,
            weight_d: '0.3',
            weight_l: '0.5',
            weight_t: '0.2 0.2 0.2 0.2',
            weight_w: '-1'
        },
        solr: {},
        lamtram: {
            word_pen: 0.0,
            beam: 5
        }
    };

    $scope.langs = {
        source: 'en',
        target: 'fr'
    };

    $scope.input = {
        translationMode: 'string', // string|xml
        strings: [''],
        file: '',
    };

    $scope.results = {
        translations: [],
        debug: ''
    };

    $scope.steps = {
        active: 1,
        progress: 1,
        templates: {
            1: 'templates/decode/config.html',
            2: 'templates/decode/settings.html',
            3: 'templates/decode/results.html'
        }
    };
    $scope.stepsTemplate = $scope.steps.templates[$scope.steps.active];

    $scope.languages =  [
        {code: 'en', name: 'English'},
        {code: 'de', name: 'German'},
        {code: 'fr', name: 'French'}
        //{code: 'it', name: 'Italian'},
        //{code: 'ru', name: 'Russian'}
    ];

    $scope.changeStep = function(index) {
        $scope.steps.active = index;
        if (index > $scope.steps.progress) {
            $scope.steps.progress = index;
        }
        $scope.stepsTemplate = $scope.steps.templates[$scope.steps.active];
    };

    $scope.onFinishedLoadingTemplate = function() {
    };

    $scope.uploadFile = function (file) {
        if (file) {
            $scope.state.progress = 1;
            file.upload = Upload.upload({
                url: config.url + 'upload',
                data: {file: file}
            });
            file.upload.then(function (response) {
                $timeout(function () {
                    console.log(response.data);
                    if (response.data.success) {
                        $scope.input.translationMode = 'xml';
                        $scope.input.file = response.data.filename;
                    } else {
                        // TODO Error server-side
                    }
                });
            }, function (response) {
                console.log(response);
                // TODO Error
            }, function (evt) {
                $scope.state.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
                $('#progress').progress('increment', $scope.state.progress);
            });
        }
    };

    $scope.getTranslations = function () {
        $scope.state.isLoading = true;
        $scope.state.loaded = false;
        var data = {
            'lang_from': $scope.langs.source,
            'lang_to': $scope.langs.target,
            'decoder': $scope.decoder.decoder,
            'decoder_settings': $scope.decoder[$scope.decoder.decoder]
        };
        var endpoint = '';
        if ($scope.input.translationMode == 'xml') {
            endpoint = config.url + 'translateXML';
            data.xml_filename = $scope.input.file;
        } else {
            endpoint = config.url + 'translateStrings';
            data.strings = $scope.input.strings;
        }
        $scope.changeStep(3)
        $http.post(endpoint, data).then(function (response) {
            console.log(response);
            $scope.results.translations = []
            for (var i = 0; i < response.data.translations.length; i++) {
                var translation = response.data.translations[i];
                if (typeof translation == 'string') {
                    $scope.results.translations.push($sce.trustAsHtml(translation));
                } else if (typeof translation == 'object') {
                    var escapedObject = {};
                    for (var key in translation) {
                        escapedObject[key] = $sce.trustAsHtml(translation[key])
                    }
                    $scope.results.translations.push(escapedObject);
                }
            }
            var debug = JSON.stringify(response.data.debug);
            debug = debug.replace(/\\n/g, '&#13;&#10;');
            debug = debug.replace(/\\t/g, '    ');
            $scope.results.debug = $sce.trustAsHtml(debug);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
        }, function (response) {
            console.log(response);
            $scope.state.isLoading = false;
        });
    };

});

/**
 * Controller for /analysis
 */
app.controller('DataAnalysisController', function ($scope, config) {

});