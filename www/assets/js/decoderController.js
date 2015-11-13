app.controller('DecoderController', function ($scope, $http, Upload, $timeout, $sce) {

    $scope.url = 'http://127.0.0.1:5050/';
    //$scope.url = 'http://diufpc114.unifr.ch:5000/'

    $scope.state = {
        isLoading: false,
        loaded: false,
        progress: 0
    };

    $scope.decoder = {
        decoder: 'moses',
        moses: {
            drop_unknown: 0,
            search_algorithm: 0,
            max_phrase_length: 20,
            verbose: 2,
            weight_d: '1',
            weight_e: '',
            weight_i: '',
            weight_l: '1',
            weight_t: '1',
            weight_w: '0'
        },
        solr: {},
        lamtram: {}
    };

    $scope.langs = {
        source: 'en',
        target: 'fr'
    };

    $scope.input = {
        mode: 'string', // string|xml
        string: ''
    };

    $scope.translationMode = 'string'; // string|xml

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


    // Methods
    // ************************

    $scope.changeStep = function(index) {
        $scope.steps.active = index;
        if (index > $scope.steps.progress) {
            $scope.steps.progress = index;
        }
        $scope.stepsTemplate = $scope.steps.templates[$scope.steps.active];
    };

    $scope.uploadFile = function (file) {
        if (file) {
            $scope.state.progress = 1;
            file.upload = Upload.upload({
                url: $scope.url + 'upload',
                data: {file: file}
            });
            file.upload.then(function (response) {
                $timeout(function () {
                    console.log(response.data);
                    if (response.data.success) {
                        $scope.data.config.mode = 'xml';
                        $scope.data.input.file = response.data.filename;
                    } else {
                        // TODO Error server-side
                    }
                });
            }, function (response) {
                console.log(response);
                // TODO Error
            }, function (evt) {
                $scope.state.progress = Math.min(100, parseInt(100.0 * evt.loaded / evt.total));
                console.log($scope.state.progress);
                $('#progress').progress('increment', $scope.state.progress);
            });
        }
    };

    $scope.getTranslations = function () {
        $scope.state.isLoading = true;
        $scope.loaded = false;
        var params = {
            'from': $scope.data.config.source_lang,
            'to': $scope.data.config.target_lang,
            'decoder': $scope.data.decoder.decoder
        };
        var endpoint = '';
        if ($scope.data.config.mode == 'xml') {
            endpoint = $scope.url + 'translateXML';
            params.xml_filename = $scope.data.input.file;
        } else {
            endpoint = $scope.url + 'get';
            params.string = $scope.data.input.string;
        }
        $http.get(endpoint, {'params': params}).then(function (response) {
            console.log(response);
            $scope.data.result.translations = response.data.translations;
            debug = JSON.stringify(response.data.debug);
            debug = debug.replace(/\\n/g, '&#13;&#10;');
            debug = debug.replace(/\\t/g, '    ');
            $scope.data.result.debug = $sce.trustAsHtml(debug);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
        }, function (response) {
            console.log(response);
            $scope.state.isLoading = false;
        });
    };

});


