<?php

use Illuminate\Support\Facades\Route;

// Servir o frontend compilado (SPA)
Route::get('/{any}', function () {
    return file_get_contents(public_path('index.html'));
})->where('any', '.*');