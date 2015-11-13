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