$(function() {

    function renderSensorChart(name, data) {
        console.log(name);
    }


    $.getJSON('/_sensors', function(sensors) {
        _.each(sensors, function(sensorName) {
            $.getJSON('/_sensor/' + sensorName, function(sensorData) {
                renderSensorChart(sensorName, sensorData);
            });
        });
    });
});