/**
 * App config
 */
app.factory('config', function() {
    var instance = {};

    instance.url = 'http://127.0.0.1:5050/';
//    instance.url = 'http://diufpc114.unifr.ch:5000/';

    return instance;
});