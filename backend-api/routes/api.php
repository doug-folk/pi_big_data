<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GameController;
use App\Http\Controllers\RatingController;

// Jogos
Route::get('games', [GameController::class, 'index']);
Route::get('games/{id}', [GameController::class, 'show']);
Route::get('games/search', [GameController::class, 'search']);
Route::get('games/discover', [GameController::class, 'discover']);


