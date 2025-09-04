<?php

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// Rotas de autenticação
Route::post('register', 'AuthController@register');
Route::post('login', 'AuthController@login');
Route::middleware('auth:sanctum')->group(function () {
    Route::post('logout', 'AuthController@logout');
    Route::get('user', 'AuthController@profile');
    Route::put('user', 'AuthController@updateProfile');

    // Favoritos
    Route::post('games/{id}/favorite', 'FavoriteController@store');
    Route::delete('games/{id}/favorite', 'FavoriteController@destroy');
    Route::get('user/favorites', 'FavoriteController@index');

    // Avaliações
    Route::post('games/{id}/ratings', 'RatingController@store');
    Route::delete('ratings/{id}', 'RatingController@destroy');
});

// Jogos (leitura)
Route::get('games', 'GameController@index');
Route::get('games/{id}', 'GameController@show');
Route::get('games/{id}/ratings', 'RatingController@index');

// Recomendações
Route::get('recommendations/user/{user_id}', 'RecommendationController@user');
Route::get('recommendations/game/{game_id}', 'RecommendationController@game');
Route::get('recommendations/mood', 'RecommendationController@mood');
Route::get('recommendations/forgotten', 'RecommendationController@forgotten');

// Descubra Novos Jogos
Route::get('games/discover', 'GameController@discover');

// Conquistas
Route::get('user/achievements', 'AchievementController@index');

// Feed de atividades
Route::get('user/activity', 'ActivityController@index');

// Comunidade
Route::get('community/lists', 'CommunityListController@index');
Route::post('community/lists', 'CommunityListController@store');
Route::post('community/lists/{id}/vote', 'CommunityListController@vote');

// Busca avançada
Route::get('games/search', 'GameController@search');
