$(function() {

    var $chartContainer = $('#chart-container')

    function removeStringData(data) {
        var stringColumns = ['component', 'timezone'];
        var doomedIndexes = [];
        var series = data.series[0];
        _.each(series.columns, function(name, index) {
            if (_.contains(stringColumns, name)) {
                doomedIndexes.push(index);
            }
        });
        // Now that we know which indexes are doomed, we reverse the order so we
        // can extract them from the list from the end
        doomedIndexes = doomedIndexes.reverse();
        _.each(doomedIndexes, function(doomed) {
            series.columns.splice(doomed, 1);
        });
        _.each(series.values, function(row) {
            _.each(doomedIndexes, function(doomed) {
                row.splice(doomed, 1);
            });
        });
    }

    function convertJsonDataToCsv(data) {
        var rows = [];
        var series = data.series[0];

        var headers = series.columns;
        var values = series.values;
        
        rows.push(headers);
        
        _.each(values, function(values) {
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
        removeStringData(data);
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
            },
            axes: {
              y2: {
                valueRange: [0.0, 1.0]
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