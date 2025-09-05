<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Favorite;
use App\Models\Game;

class FavoriteController extends Controller
{
    public function index(Request $request)
    {
        $favorites = $request->user()->favorites()->with('game')->get();
    return response()->json(['data' => $favorites]);
    }

    public function store(Request $request, $game_id)
    {
        $favorite = Favorite::firstOrCreate([
            'user_id' => $request->user()->id,
            'game_id' => $game_id,
        ]);
    return response()->json(['favorite' => $favorite], 201);
    }

    public function destroy(Request $request, $game_id)
    {
        $favorite = Favorite::where('user_id', $request->user()->id)
            ->where('game_id', $game_id)->first();
        if ($favorite) {
            $favorite->delete();
        }
        return response()->json(['message' => 'Removido dos favoritos']);
    }
}
