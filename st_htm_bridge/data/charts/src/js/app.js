angular.module('app', [
  'ui.bootstrap',
  'templates',
  'ui.router',
  'home',
  'sensors',
  'pageNotFound'
]);

// some Settings:
angular.module('app').constant('CONFIG', {
  'STRING_COLUMNS': ['component', 'timezone'],
  'LIMIT_OPTIONS': [100, 500, 1000, 5000, 10000, 50000],
  'AGGREGATE_OPTIONS' : [
    {
      label : 'seconds',
      value : 's'
    },
    {
      label : 'minutes',
      value : 'm'
    },
    {
      label : 'hours',
      value : 'h'
    },
    {
      label : 'days',
      value : 'd'
    },
    {
      label : 'weeks',
      value : 'w'
    }
  ],
  'SINCE_OPTIONS': [{
    number: 10,
    units: 'minutes'
  }, {
    number: 1,
    units: 'hour'
  }, {
    number: 3,
    units: 'hours'
  }, {
    number: 6,
    units: 'hours'
  }, {
    number: 12,
    units: 'hours'
  }, {
    number: 1,
    units: 'day'
  }, {
    number: 3,
    units: 'days'
  }, {
    number: 1,
    units: 'week'
  }, {
    number: 2,
    units: 'weeks'
  }, {
    number: 1,
    units: 'month'
  }, {
    number: 3,
    units: 'months'
  }],
  'CHART_FIELDS': {
    'anomalyScore': {
      color: 'rgb(201,12,6)'
    },
    'anomalyLikelihood': {
      color: 'rgb(204,122,5)'
    },
    'value': {
      color: 'rgb(4,138,191)'
    }
  },
  'ANOMALY_THRESHOLD': 0.9,
  'THRESHOLD_HIGHLIGHT_FIELDS': ["anomalyScore", "anomalyLikelihood"]
});

angular.module('app').config(['$stateProvider', '$urlRouterProvider', function($stateProvider, $urlRouterProvider) {
  // set up the states
  $stateProvider
    .state('home', {
      url: "/",
      templateUrl: "routes/home/home.tpl.html",
      controller: "HomeController"
    })
    .state('pageNotFound', {
      url: "/pageNotFound",
      templateUrl: "routes/pageNotFound/pageNotFound.tpl.html",
      controller: "PageNotFoundController"
    });
  // For any unmatched url, redirect to page not found
  $urlRouterProvider.when('', '/');
  $urlRouterProvider.otherwise('/pageNotFound');
}]);

angular.module('templates', []);
