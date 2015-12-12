$(function() {

    $chartContainer = $('#chart-container')

    function convertJsonDataToCsv(data) {
        var rows = [];
        var series = data.series[0];
        series.columns.splice(3, 1);
        var headers = series.columns;
        var values = series.values;
        rows.push(headers);
        _.each(values, function(values) {
            values.splice(3, 1);
            rows.push(values.join(','));
        });
        return rows.join('\n');
    }

    function prepareChartMarkup(id, name) {
        var $header = $('<h3>' + name + '</h3>');
        var $chart = $('<div></div>', {id: id, class: 'chart'});
        $chartContainer.append($header)
                       .append($chart);
    }

    function renderChart(id, data) {
        var el = document.getElementById(id);
        var csvString = convertJsonDataToCsv(data);
        return new Dygraph(el, csvString, {
            width: 1000,
            series: {
              anomalyScore: {
                axis: 'y2',
                color: 'orange'
              },
              anomalyLikelihood: {
                axis: 'y2',
                color: 'red'
              }
            }
        });
    }

    function renderSensorChart(name, data) {
        console.log(name);
        var id = name.replace('/', '_').replace(/\+/g, '-');
        prepareChartMarkup(id, name);
        renderChart(id, data);
    }


    $.getJSON('/_sensors', function(sensors) {
        _.each(sensors, function(sensorName) {
            $.getJSON('/_sensor/' + sensorName, function(sensorData) {
                renderSensorChart(sensorName, sensorData);
            });
        });
    });
});