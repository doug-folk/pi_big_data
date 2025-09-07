<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GameController;

Route::middleware([])->group(function() {
    Route::get('games/search', [GameController::class, 'search']);
    Route::get('games/discover', [GameController::class, 'discover']);
    Route::get('games/{id}', [GameController::class, 'show']);
    Route::get('games', [GameController::class, 'index']);
});

