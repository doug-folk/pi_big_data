<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\AuthController;
use App\Http\Controllers\GameController;
use App\Http\Controllers\FavoriteController;
use App\Http\Controllers\RatingController;
use App\Http\Controllers\ActivityController;
use App\Http\Controllers\CommunityListController;


// Autenticação
Route::post('register', [AuthController::class, 'register']);
Route::post('login', [AuthController::class, 'login']);

Route::middleware('auth:sanctum')->group(function () {
    Route::post('logout', [AuthController::class, 'logout']);
    Route::get('profile', [AuthController::class, 'profile']);
    Route::put('profile', [AuthController::class, 'updateProfile']);

    // Jogos
    Route::get('games', [GameController::class, 'index']);
    Route::get('games/{id}', [GameController::class, 'show']);
    Route::get('games/search', [GameController::class, 'search']);

    // Favoritos
    Route::post('games/{id}/favorite', [FavoriteController::class, 'store']);
    Route::delete('games/{id}/favorite', [FavoriteController::class, 'destroy']);

    // Avaliações
    Route::post('games/{id}/rate', [RatingController::class, 'store']);
    Route::put('games/{id}/rate', [RatingController::class, 'update']);

    // Feed de atividades
    Route::get('feed', [ActivityController::class, 'index']);

    // Listas da comunidade
    Route::get('community-lists', [CommunityListController::class, 'index']);
    Route::post('community-lists', [CommunityListController::class, 'store']);
    Route::post('community-lists/{id}/games', [CommunityListController::class, 'addGame']);
});

