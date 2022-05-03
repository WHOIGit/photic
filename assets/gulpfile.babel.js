'use strict';

import plugins       from 'gulp-load-plugins';
import yargs         from 'yargs';
import browser       from 'browser-sync';
import gulp          from 'gulp';
import rimraf        from 'rimraf';
import yaml          from 'js-yaml';
import fs            from 'fs';
import webpackStream from 'webpack-stream';
import webpack2      from 'webpack';
import named         from 'vinyl-named';
import autoprefixer  from 'autoprefixer';
import imagemin      from 'gulp-imagemin';

const sass = require('gulp-sass')(require('sass'));
const postcss = require('gulp-postcss');
const uncss = require('postcss-uncss');
// Load all Gulp plugins into one variable
const $ = plugins();
// Check for --production flag
const PRODUCTION = !!(yargs.argv.production);

// Load settings from settings.yml
function loadConfig() {
  const unsafe = require('js-yaml-js-types').all;
  const schema = yaml.DEFAULT_SCHEMA.extend(unsafe);
  const ymlFile = fs.readFileSync('config.yml', 'utf8');
  return yaml.load(ymlFile, {schema});
}
const { PORT, UNCSS_OPTIONS, PATHS } = loadConfig();

console.log(UNCSS_OPTIONS);

// Build the "dist" folder by running all of the below tasks
// Sass must be run later so UnCSS can search for used classes in the others assets.
gulp.task('build',
 gulp.series(clean, gulp.parallel(javascript, images, copy, icons, vendorCSS, django), sassBuild));

// Build the site, run the server, and watch for file changes
gulp.task('default',
  gulp.series('build', watch));

// Delete the "dist" folder
// This happens every time a build starts
function clean(done) {
  rimraf(PATHS.dist, done);
}

function icons() {
    return gulp.src('node_modules/@fortawesome/fontawesome-free/webfonts/*')
        .pipe(gulp.dest(PATHS.dist+'/fonts/'));
}

function vendorCSS(){
    return gulp.src('node_modules/jquery-datetimepicker/build/jquery.datetimepicker.min.css')
    .pipe(gulp.dest(PATHS.dist+'/vendorCSS/'));
}

// Copy files out of the assets folder
// This task skips over the "img", "js", and "scss" folders, which are parsed separately
function copy() {
  return gulp.src(PATHS.assets)
    .pipe(gulp.dest(PATHS.dist));
}

// Compile Sass into CSS
// In production, the CSS is compressed
function sassBuild() {

  const postCssPlugins = [
    // Autoprefixer
    autoprefixer(),
    // UnCSS - Uncomment to remove unused styles in production
    // PRODUCTION && uncss(UNCSS_OPTIONS),
  ].filter(Boolean);

  return gulp.src('src/scss/app.scss')
    .pipe($.sourcemaps.init())
    .pipe(sass({
      includePaths: PATHS.sass
    }))
    .pipe(postcss(postCssPlugins))
    .pipe($.if(PRODUCTION, $.cleanCss({ compatibility: 'ie11' })))
    .pipe($.if(!PRODUCTION, $.sourcemaps.write()))
    .pipe(gulp.dest(PATHS.dist + '/css'))
    .pipe(browser.reload({ stream: true }));
}

let webpackConfig = {
  mode: (PRODUCTION ? 'production' : 'development'),
  module: {
    rules: [
      {
        test: /\.js$/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [ "@babel/preset-env" ],
            compact: false
          }
        }
      }
    ]
  },
  devtool: !PRODUCTION && 'source-map'
}

// Combine JavaScript into one file
// In production, the file is minified
function javascript() {
  return gulp.src(PATHS.entries)
    .pipe(named())
    .pipe($.sourcemaps.init())
    .pipe(webpackStream(webpackConfig, webpack2))
    .pipe($.if(PRODUCTION, $.terser()
      .on('error', e => { console.log(e); })
    ))
    .pipe($.if(!PRODUCTION, $.sourcemaps.write()))
    .pipe(gulp.dest(PATHS.dist + '/js'));
}

// Copy images to the "dist" folder
// In production, the images are compressed
function images() {
  return gulp.src('src/img/**/*')
    .pipe($.if(PRODUCTION, imagemin([
      imagemin.gifsicle({interlaced: true}),
      imagemin.mozjpeg({quality: 85, progressive: true}),
      imagemin.optipng({optimizationLevel: 5}),
      imagemin.svgo({
        plugins: [
          {removeViewBox: true},
          {cleanupIDs: false}
        ]
      })
    ])))
    .pipe(gulp.dest(PATHS.dist + '/img'));
}

// Copy Django admin static files (from running collectstatic)
function django() {
  return gulp.src('django/admin/**/*')
      .pipe(gulp.dest(PATHS.dist + '/admin'));
}

// Start a server with BrowserSync to preview the site in
function server(done) {
  browser.init({
    server: PATHS.dist, port: PORT
  }, done);
}

// Reload the browser with BrowserSync
function reload(done) {
  browser.reload();
  done();
}

// Watch for changes to static assets, pages, Sass, and JavaScript
function watch() {
  gulp.watch(PATHS.assets, copy);
  gulp.watch('src/scss/**/*.scss').on('all', sass);
  gulp.watch('src/js/**/*.js').on('all', gulp.series(javascript, browser.reload));
  gulp.watch('src/img/**/*').on('all', gulp.series(images, browser.reload));
}
