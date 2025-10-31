<?php

use Illuminate\Support\Facades\Route;

Route::get('/', function () {
    $frontendUrl = config('app.frontend_url', 'http://localhost:3000');

    return redirect()->away($frontendUrl);
});
