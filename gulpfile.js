var gulp = require('gulp');
var stylish = require('jshint-stylish');
var jshint = require('gulp-jshint');
var uglify = require('gulp-uglify');
var concat = require('gulp-concat');
var less = require('gulp-less');
var path = require('path');
var minifyCSS = require('gulp-minify-css');
var del = require('del');
var karmaServer = require('karma').Server;

var appName = "smartthings.htm.bridge";

var appJS = [
  "charts/src/js/**/*.js"
];

var externalJS = [
  "charts/bower_components/jquery/dist/jquery.min.js",
  "charts/bower_components/angular/angular.min.js",
  "charts/bower_components/angular-bootstrap/ui-bootstrap-tpls.min.js",
  "charts/bower_components/bootstrap/dist/js/bootstrap.min.js",
  "charts/bower_components/dygraphs/dygraph-combined.js",
  "charts/bower_components/moment/min/moment.min.js",
  "charts/bower_components/lodash/lodash.min.js"
];

gulp.task('default', ['build']);

gulp.task('build', ['externaljs', 'appjs', 'less', 'static']);

gulp.task('clean', function() {
  return del(['static/*']);
});

gulp.task('appjs', ['clean'], function() {
  return gulp.src(appJS)
    .pipe(jshint())
    .pipe(jshint.reporter('default'))
    .pipe(concat('app.js'))
    .pipe(uglify())
    .pipe(gulp.dest('static'));
});

gulp.task('externaljs', ['clean'], function() {
  return gulp.src(externalJS)
    .pipe(concat("external.js"))
    .pipe(gulp.dest('static'));
});

gulp.task('less', ['clean'], function() {
  return gulp.src('charts/src/less/stylesheet.less')
    .pipe(less({
      paths: [
        path.join(__dirname, 'charts', 'bower_components', 'bootstrap', 'less'),
        path.join(__dirname, 'charts', 'src', 'less')
      ]
    }))
    .pipe(minifyCSS())
    .pipe(gulp.dest('static'));
});

var files = [
  //'client/src/index.html',
  //'client/src/assets/*'
];

var fonts = ['charts/bower_components/bootstrap/fonts/*'];

gulp.task('static', ['assets', 'fonts']);

gulp.task('assets', ['clean'], function(){
  return gulp.src(files)
    .pipe(gulp.dest('build'))
});

gulp.task('fonts', ['clean'], function(){
  return gulp.src(fonts)
    .pipe(gulp.dest('static/fonts'))
});
/*
gulp.task('test', function (done) {
  new karmaServer({
    configFile: __dirname + '/charts/test/karma.conf.js',
    singleRun: true
  }, done).start();
});
*/
