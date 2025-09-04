<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class AdminController extends Controller
{
    public function stats()
    {
        $users = \App\Models\User::count();
        $games = \App\Models\Game::count();
        $ratings = \App\Models\Rating::count();
        $favorites = \App\Models\Favorite::count();
        $achievements = \App\Models\Achievement::count();
        return response()->json(compact('users', 'games', 'ratings', 'favorites', 'achievements'));
    }

    public function users()
    {
        $users = \App\Models\User::paginate(20);
        return response()->json($users);
    }
}
