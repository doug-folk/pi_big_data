<?php

use Illuminate\Support\Facades\Route;

// Fallback para o Vite SPA
Route::get('/{any}', function () {
    return file_get_contents(public_path('index.html'));
})->where('any', '.*');