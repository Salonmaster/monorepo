// webpack.mix.js

let mix = require('laravel-mix');

mix.sass("resources/css/frontend/styles.scss", 'css/frontend.css').options({
    autoprfixer: { remove: false}
})
mix.sass("resources/css/backend/styles.scss", 'css/backend.css').options({
    autoprfixer: { remove: false}
})