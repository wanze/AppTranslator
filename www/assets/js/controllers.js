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

    $scope.languages =  [
        {code: 'en', name: 'English'},
        {code: 'de', name: 'German'},
        {code: 'fr', name: 'French'}
        //{code: 'it', name: 'Italian'},
        //{code: 'ru', name: 'Russian'}
    ];

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
        solr: {
            rows: 100
        },
        lamtram: {
            word_pen: 0.0,
            beam: 5
        },
        tensorflow: {
            num_layers: 2,
            size: 256
        },
        compare: {},
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
        debug: '',
        columns: []
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
        var decoder = $scope.decoder.decoder;
        var settings = (decoder == 'compare') ? $scope.decoder : $scope.decoder[decoder]
        var data = {
            'lang_from': $scope.langs.source,
            'lang_to': $scope.langs.target,
            'decoder': $scope.decoder.decoder,
            'decoder_settings': settings
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
            var columns = ['Input', 'Output']
            var decoders = ['Output Moses', 'Output Tensorflow', 'Output Solr'];
            if ($scope.input.translationMode == 'string' && $scope.decoder.decoder == 'compare') {
                columns = ['Input'].concat(decoders)
            } else if ($scope.input.translationMode == 'xml') {
                columns = ['Key', 'Source'];
                if ($scope.decoder.decoder == 'compare') {
                    columns = columns.concat(decoders);
                } else {
                    columns = columns.concat(['Output']);
                }
            }
            $scope.results.columns = columns;
            var sorting = {'key': 0, 'source': 1, 'target': 2, 'moses': 3, 'tensorflow' : 4, 'solr' : 5};
            for (var i = 0; i < response.data.translations.length; i++) {
                var translation = response.data.translations[i];
                if (typeof translation == 'string') {
                    var row = [$sce.trustAsHtml($scope.input.strings[i]), $sce.trustAsHtml(translation)]
                    $scope.results.translations.push(row);
                } else if (typeof translation == 'object') {
                    var row = [];
                    for (var key in translation) {
                        var sort = sorting[key];
                        var value = translation[key] || '&nbsp;';
                        row[sort] = $sce.trustAsHtml(value);
                    }
                    // row.filter -> shortest way to re-index array
                    $scope.results.translations.push(row.filter(function(val) {return val;}));
                }
            }
            console.log($scope.results);
            var debug = response.data.debug;
            debug = debug.replace(/\\n/g, '&#13;&#10;');
            debug = debug.replace(/\\t/g, '    ');
            $scope.results.debug = $sce.trustAsHtml(debug);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
            $('.secondary.pointing.menu .item').tab();
        }, function (response) {
            console.log(response);
            $scope.state.isLoading = false;
        });
    };

});

/**
 * Controller for /analysis
 */
app.controller('DataAnalysisController', function ($scope, config, $http) {

    $('.secondary.pointing.menu .item').tab();

    $scope.top_terms = {
        'lang': 'en',
        'terms': [],
    };

    $scope.term_variations = {
        'source': 'en',
        'target': 'fr',
        'term': '',
        'variations': []
    };

    $scope.state = {
        isLoading: false,
        loaded: false
    };

    $scope.drawChart = function() {
        Chart.defaults.global.responsive = true;
        var counts = [];
        var labels = [];
        for (var i = 0; i < $scope.top_terms.terms.length; i++) {
            counts.push($scope.top_terms.terms[i].count);
            labels.push('');
        }
        var data = {
            labels: labels,
            datasets: [
                {
                    label: 'Terms',
                    fillColor: "rgba(220,220,220,0.2)",
                    strokeColor: "rgba(220,220,220,1)",
                    pointColor: "rgba(220,220,220,1)",
                    pointStrokeColor: "#fff",
                    pointHighlightFill: "#fff",
                    pointHighlightStroke: "rgba(220,220,220,1)",
                    data: counts
                }
            ]
        }
        var ctx = document.getElementById("top-terms-chart").getContext("2d");
        var chart = new Chart(ctx).Line(data);
    };


    $scope.getTermVariations = function() {
        $scope.state.isLoading = true;
        var url = config.url + 'getTermVariations';
        var conf = {
            params: {
                'source': $scope.term_variations.source,
                'target': $scope.term_variations.target,
                'term': $scope.term_variations.term
            }
        };
        $http.get(url, conf).then(function (response) {
            console.log(response);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
            $scope.term_variations.variations = response.data;
        });
    };

    $scope.getTopTerms = function() {
        $scope.state.isLoading = true;
        var url = config.url + 'getTopTerms';
        var conf = {
            params: {
                'lang': $scope.top_terms.lang
            }
        };
        $http.get(url, conf).then(function (response) {
            console.log(response);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
            $scope.top_terms.terms = response.data;
            $scope.drawChart();
        });
    };

});