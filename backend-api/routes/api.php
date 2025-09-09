<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\GameController;

Route::middleware([])->group(function() {
    // Busca por texto
    Route::get('games/search', [GameController::class, 'search']);
    // Descoberta aleatória
    Route::get('games/discover', [GameController::class, 'discover']);
    // Detalhes de um jogo
    Route::get('games/{id}', [GameController::class, 'show']);
    // Lista todos os jogos
    Route::get('games', [GameController::class, 'index']);

    // Recomendações (exemplo, precisa implementar os métodos no controller)
    Route::get('games/recommend/by-mood', [GameController::class, 'recommendByMood']);
    Route::get('games/recommend/for-game/{game_id}', [GameController::class, 'recommendForGame']);
    Route::get('games/discover/by-filter', [GameController::class, 'discoverByFilter']);
    Route::get('games/discover/random', [GameController::class, 'discoverRandom']);
    Route::get('games/discover/by-cluster/{game_id}', [GameController::class, 'discoverByCluster']);
});

