var app = angular.module('appTranslator', []);

app.controller('TranslationController', function($scope, $http) {

    var url = 'http://127.0.0.1:5000/translate';

    $scope.state = {
        isLoading : false,
        loaded : false
    }

    $scope.data = {
        string : '',
        source_lang : '',
        target_lang : '',
        translations : [],
        debug : '',
    };

    $scope.getTranslations = function() {
        $scope.isLoading = true;
        var params = {
            'from' : $scope.data.source_lang,
            'to' : $scope.data.target_lang,
            'string' : $scope.data.string
        };
        $http.get(url, {'params':  params}).then(function(response) {
            console.log(response);
            $scope.data.translations = response.data.translations;
            $scope.data.debug = JSON.stringify(response.data.debug);
            $scope.state.isLoading = false;
            $scope.state.loaded = true;
        }, function(response) {
            console.log(response);
            $scope.state.isLoading = false;
        });
    };

    $scope.getLanguages = function() {
        return [
            {code : 'en', name: 'English'},
            {code : 'de', name: 'German'},
            {code : 'fr', name: 'French'},
            {code : 'it', name: 'Italian'},
            {code : 'ru', name: 'Russian'}
        ];
    };
    $scope.data.languages = $scope.getLanguages();

});


