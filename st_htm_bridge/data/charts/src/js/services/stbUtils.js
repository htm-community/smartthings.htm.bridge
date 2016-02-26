angular.module('app').factory('stbUtils', function(){

  var service = {
    getUrlQueryString : function() {
        var questionMarkIndex = window.location.href.indexOf('?');
        var queryString = '';
        if (questionMarkIndex > 1) {
            queryString = window.location.href.slice(window.location.href.indexOf('?') + 1);
        }
        return queryString;
    },
    getUrlVars : function() {
        var vars = [], hash;
        var hashes = getUrlQueryString().split('&');
        for(var i = 0; i < hashes.length; i++)
        {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = hash[1];
        }
        return vars;
    }
  };

  return service;
});
