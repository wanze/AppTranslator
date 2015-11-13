var app = angular.module('appTranslator', ['ngRoute', 'ngFileUpload']);

app.config(['$routeProvider',
    function($routeProvider) {
        $routeProvider.
            when('/decode', {
                templateUrl: 'templates/decode/index.html',
                controller: 'DecoderController'
            }).
            when('/analysis', {
                templateUrl: 'templates/analysis/analysis.html',
                controller: 'DataAnalysisController'
            }).
            otherwise({
                redirectTo: '/decode'
            });
    }
]);