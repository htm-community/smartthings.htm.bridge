angular.module('app', ['ui.bootstrap','templates']);

// some Settings:
angular.module('app').constant('CONFIG', {
  'STRING_COLUMNS' : ['component', 'timezone'],
  'LIMIT_OPTIONS' : [100,500,1000,5000,10000,50000]
});

angular.module('templates', []);

