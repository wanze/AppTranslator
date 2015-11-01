var app = angular.module('appTranslator', ['ngFileUpload']);

app.controller('TranslationController', function ($scope, $http, Upload, $timeout, $sce) {

    $scope.url = 'http://127.0.0.1:5050/';

    $scope.state = {
        isLoading: false,
        loaded: false,
        progress: 0
    };

    $scope.data = {
        decoder: {
            decoder: 'moses',
            moses: {},
            solr: {}
        },
        config: {
            source_lang: 'en',
            target_lang: 'fr',
            mode: 'string' // string|xml
        },
        input: {
            string: '',
            file: ''
        },
        result: {
            translations: [],
            debug: ''
        }
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
            'to': $scope.data.config.target_lang
        };
        var endpoint = '';
        if ($scope.data.config.mode == 'xml') {
            endpoint = $scope.url + 'translateXML'
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

    $scope.getLanguages = function () {
        return [
            {code: 'en', name: 'English'},
            {code: 'de', name: 'German'},
            {code: 'fr', name: 'French'},
            {code: 'it', name: 'Italian'},
            {code: 'ru', name: 'Russian'}
        ];
    };
    $scope.data.languages = $scope.getLanguages();

});


