angular.module("app",["ui.bootstrap"]),angular.module("app").controller("appCtrl",["$scope","$http","$timeout",function(e,n,i){e.view={fieldState:[],graph:null,dataField:null,optionsVisible:!0,filePath:"",loadedFileName:"",errors:[],loading:!1};var t=[],a=[],r=[],l={},o=!1,s=0;e.toggleOptions=function(){e.view.optionsVisible=!e.view.optionsVisible,e.view.graph&&(l.resize=i(function(){e.view.graph.resize()}))},e.getRemoteFile=function(){e.$broadcast("fileUploadChange"),e.view.loading=!0,n.head(e.view.filePath,{headers:{Range:"bytes=0-32"}}).then(function(n){206===n.status?d(e.view.filePath):g(e.view.filePath)},function(){g(e.view.filePath)})},e.canDownload=function(){var n=e.view.filePath.split("://");return("https"===n[0]||"http"===n[0])&&n.length>1&&n[1].length>0?!0:!1},e.getLocalFile=function(n){e.view.filePath=n.target.files[0].name,e.view.loading=!0,h(n.target.files[0])};var p=function(e){var n=e.split("/");return n[n.length-1]},u=function(n){for(var i=0;i<n.length;i++){for(var l=[],p=0;p<a.length;p++){var u=a[p],f=o&&u===appConfig.TIMESTAMP?s++:n[i][u];u===appConfig.TIMESTAMP?"number"==typeof f||("string"==typeof f&&null!==v(f)?f=v(f):(c("Parsing timestamp failed, fallback to using iteration number","warning",!0),f=s)):"None"===f&&(f=appConfig.NONE_VALUE_REPLACEMENT),l.push(f)}appConfig.SLIDING_WINDOW&&t.length>appConfig.BUFFER_SIZE&&(t.shift(),r.shift()),t.push(l),r.push(angular.extend([],l))}null===e.view.graph?E():e.view.graph.updateOptions({file:t}),e.$apply()},f=function(){e.view.fieldState.length=0,e.view.graph=null,e.view.dataField=null,e.view.errors.length=0,e.view.loadedFileName="",o=!1,s=0,t.length=0,a.length=0},g=function(n){f(),Papa.parse(n,{download:!0,skipEmptyLines:!0,header:!0,dynamicTyping:!0,worker:!1,comments:"#",complete:function(i){angular.isDefined(i.data)?(e.view.loadedFileName=p(n),a=S(i.data[i.data.length-1],appConfig.EXCLUDE_FIELDS),i.data.splice(0,appConfig.HEADER_SKIPPED_ROWS),u(i.data)):c("An error occurred when attempting to download file.","danger"),e.view.loading=!1,e.$apply()},error:function(n){c("Could not download file.","danger"),e.view.loading=!1}})},d=function(n){f(),Papa.RemoteChunkSize=appConfig.REMOTE_CHUNK_SIZE;var i=!1;Papa.parse(n,{download:!0,skipEmptyLines:!0,header:!0,dynamicTyping:!0,worker:!1,comments:"#",chunk:function(e){i||(a=S(e.data[e.data.length-1],appConfig.EXCLUDE_FIELDS),i=!0),u(e.data)},beforeFirstChunk:function(i){e.view.loadedFileName=p(n);var t=i.split(/\r\n|\r|\n/);return t.splice(1,appConfig.HEADER_SKIPPED_ROWS),e.view.loading=!1,t.join("\n")},error:function(n){c("Could not stream file.","danger"),e.view.loading=!1}})},h=function(n){f(),Papa.LocalChunkSize=appConfig.LOCAL_CHUNK_SIZE;var i=!1;Papa.parse(n,{skipEmptyLines:!0,header:!0,dynamicTyping:!0,worker:!1,comments:"#",chunk:function(e){i||(a=S(e.data[e.data.length-1],appConfig.EXCLUDE_FIELDS),i=!0),u(e.data)},beforeFirstChunk:function(i){e.view.loadedFileName=n.name;var t=i.split(/\r\n|\r|\n/);return t.splice(1,appConfig.HEADER_SKIPPED_ROWS),e.view.loading=!1,t.join("\n")},error:function(n){c(n,"danger"),e.view.loading=!1}})},c=function(n,i,t){if(t="undefined"!=typeof t?t:!1,exists=!1,t){errs=e.view.errors;for(var a=0;a<errs.length;a++)if(errs[a].message===n)return}e.view.errors.push({message:n,type:i}),e.$apply()};e.clearErrors=function(){e.view.errors.length=0},e.clearError=function(n){e.view.errors.splice(n,1)};var v=function(e){var n=new Date(e);if("Invalid Date"!==n.toString())return n;var i=String(e).split(" "),t=[],a=i[0].split("/"),r=i[0].split("-");if(1===a.length&&1===r.length||a.length>1&&r.length>1)return c("Could not parse the timestamp","warning",!0),null;if(r.length>2)t.push(r[0]),t.push(r[1]),t.push(r[2]);else{if(!(a.length>2))return c("There was something wrong with the date in the timestamp field.","warning",!0),null;t.push(a[2]),t.push(a[0]),t.push(a[1])}if(i[1]){var l=i[1].split(":");t=t.concat(l)}for(var o=0;o<t.length;o++)t[o]=parseInt(t[o]);return n=new Function.prototype.bind.apply(Date,[null].concat(t)),"Invalid Date"===n.toString()?(c("The timestamp appears to be invalid.","warning",!0),null):n};e.normalizeField=function(n){var i=n+1;if(null===e.view.dataField)return void console.warn("No data field is set");for(var a=parseInt(e.view.dataField)+1,r=function(e,n){return Math[n].apply(null,e)},l=[],o=[],s=0;s<t.length;s++)"number"==typeof t[s][a]&&"number"==typeof t[s][i]&&(l.push(t[s][a]),o.push(t[s][i]));for(var p=r(l,"max")-r(l,"min"),u=r(o,"max")-r(o,"min"),f=p/u,g=0;g<t.length;g++)t[g][i]=parseFloat((t[g][i]*f).toFixed(10));e.view.graph.updateOptions({file:t})},e.denormalizeField=function(n){for(var i=n+1,a=0;a<t.length;a++)t[a][i]=r[a][i];e.view.graph.updateOptions({file:t})},e.renormalize=function(){for(var n=0;n<e.view.fieldState.length;n++)e.view.fieldState[n].normalized&&e.normalizeField(e.view.fieldState[n].id)};var w=function(n,i){for(var t=0;t<e.view.fieldState.length;t++)if(e.view.fieldState[t].name===n){e.view.fieldState[t].value=i;break}},m=function(n){for(var i=0;i<n.length;i++)e.view.fieldState[i].color=n[i]},S=function(e,n){e.hasOwnProperty(appConfig.TIMESTAMP)||(c("No timestamp field was found, using iterations instead","info"),o=!0);var i=[];return angular.forEach(e,function(e,t){"number"==typeof e&&-1===n.indexOf(t)&&t!==appConfig.TIMESTAMP&&i.push(t)}),i.unshift(appConfig.TIMESTAMP),i};e.toggleVisibility=function(n){e.view.graph.setVisibility(n.id,n.visible),n.visible||(n.value=null)},e.showHideAll=function(n){for(var i=0;i<e.view.fieldState.length;i++)e.view.fieldState[i].visible=n,e.view.graph.setVisibility(e.view.fieldState[i].id,n),n||(e.view.fieldState[i].value=null)};var E=function(){var n=document.getElementById("dataContainer");e.view.fieldState.length=0,e.view.dataField=null;for(var i=0,r=o,l=0;l<a.length;l++){var s=a[l];s===appConfig.TIMESTAMP||r?r=!1:(e.view.fieldState.push({name:s,id:i,visible:!0,normalized:!1,value:null,color:"rgb(0,0,0)"}),i++)}e.view.graph=new Dygraph(n,t,{labels:a,labelsUTC:!1,showLabelsOnHighlight:!1,xlabel:"Time",ylabel:"Values",strokeWidth:1,pointClickCallback:function(e,n){timestamp=moment(n.xval),timestampString=timestamp.format("YYYY-MM-DD HH:mm:ss.SSS000"),window.prompt("Copy to clipboard: Ctrl+C, Enter",timestampString)},animatedZooms:!0,showRangeSelector:"RangeSelector"===appConfig.ZOOM,highlightCallback:function(n,i,t,a,r){for(var l=0;l<t.length;l++)w(t[l].name,t[l].yval);e.$apply()},drawCallback:function(e,n){n&&m(e.getColors())}})};e.$on("$destroy",function(){angular.forEach(l,function(e){i.cancel(e)})})}]),$(function(){function e(){var e=window.location.href.indexOf("?"),n="";return e>1&&(n=window.location.href.slice(window.location.href.indexOf("?")+1)),n}function n(){for(var n,i=[],t=e().split("&"),a=0;a<t.length;a++)n=t[a].split("="),i.push(n[0]),i[n[0]]=n[1];return i}window.STHTMB={utils:{getUrlQueryString:e,getUrlVars:n}}}),angular.module("app").directive("stbChart",["$http","stbUtils",function(e,n){return{restrict:"EA",scope:{sensorName:"@",sensorSince:"@",maxRows:"@"},replace:!0,template:"<div class='chart'></div>",link:function(n,i,t){n.view={chart:null};var a,r=function(e){var n=["component","timezone"],i=[],t=e.series[0];angular.forEach(t.columns,function(e,t){-1!==n.indexOf(e)&&i.push(t)}),i=i.reverse(),angular.forEach(i,function(e){t.columns.splice(e,1)}),angular.forEach(t.values,function(e){angular.forEach(i,function(n){e.splice(n,1)})})},l=function(e){var n=new Date(e);if("Invalid Date"!==n.toString())return n;var i=String(e).split(" "),t=[],a=i[0].split("/"),r=i[0].split("-");if(1===a.length&&1===r.length||a.length>1&&r.length>1)return p("Could not parse the timestamp","warning",!0),null;if(r.length>2)t.push(r[0]),t.push(r[1]),t.push(r[2]);else{if(!(a.length>2))return p("There was something wrong with the date in the timestamp field.","warning",!0),null;t.push(a[2]),t.push(a[0]),t.push(a[1])}if(i[1]){var l=i[1].split(":");t=t.concat(l)}for(var o=0;o<t.length;o++)t[o]=parseInt(t[o]);return n=new Function.prototype.bind.apply(Date,[null].concat(t)),"Invalid Date"===n.toString()?(p("The timestamp appears to be invalid.","warning",!0),null):n},o=function(e){var n=0;for(a=0;a<e.series[0].columns.length;a++)if("time"===e.series[0].columns[a]||"timestamp"===e.series[0].columns[a]){n=a;break}for(a=0;a<e.series[0].values.length;a++)e.series[0].values[a][n]=l(e.series[0].values[a][n]);return e},s=function(){var i="/_data/sensor/"+n.sensorName+"?limit=100";e.get(i).then(function(e){r(e.data),o(e.data),n.view.chart=u(e.data)},p)},p=function(e){console.log(e)},u=function(e){return new Dygraph(i[0],e.series[0].values,{labels:e.series[0].columns,series:{value:{strokeWidth:2,strokePattern:[4,1]},anomalyScore:{axis:"y2",color:"orange"},anomalyLikelihood:{axis:"y2",color:"red"}},axes:{y2:{valueRange:[0,1.1]}},legend:"follow",labelsSeparateLines:!0})};s()}}}]),angular.module("app").factory("stbUtils",function(){var e={getUrlQueryString:function(){var e=window.location.href.indexOf("?"),n="";return e>1&&(n=window.location.href.slice(window.location.href.indexOf("?")+1)),n},getUrlVars:function(){for(var e,n=[],i=getUrlQueryString().split("&"),t=0;t<i.length;t++)e=i[t].split("="),n.push(e[0]),n[e[0]]=e[1];return n}};return e});