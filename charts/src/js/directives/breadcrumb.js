angular.module('app').directive('breadcrumb', ['$state', function($state) {
  return {
    restrict: 'E',
    replace: true,
    templateUrl: "directives/breadcrumb.tpl.html",
    link: function(scope, element, attrs) {

      // TODO: Make this more abstracted and better

      scope.breadcrumbs = [];

      scope.$on('$stateChangeSuccess', function(event, toState, toParams){
        scope.breadcrumbs.length = 0;
        if ($state.current.name === 'sensors.list') {
          scope.breadcrumbs.push({
            name : "Sensors",
              state : "sensors.list",
              active : true
            }
          );
        } else if ($state.current.name === 'sensors.type.sensor') {
          scope.breadcrumbs.push(
            { name : "Sensors",
              state : "sensors.list",
              active : false
            }
          );
          scope.breadcrumbs.push(
            { name : toParams.type + "/" + toParams.sensor,
              state : "sensors.type.sensor({ type: '" + toParams.type + "', sensor: '" + toParams.sensor + "' })",
              active : true
            }
          );
        }
      });
    }
  };
}]);
