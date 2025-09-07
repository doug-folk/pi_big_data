<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Game;

class GameController extends Controller
{
    public function index(Request $request)
    {
        $games = Game::all(); // Retorna todos
        return response()->json(['data' => $games]);
    }

    public function show($id)
    {
        $game = Game::findOrFail($id);
        return response()->json([
            'game' => [
                'id' => $game->id,
                'title' => $game->title,
                'name' => $game->name,
                'url' => $game->url,
                'reviews' => $game->reviews,
                'genre' => $game->genre,
                'categoria' => $game->categoria,
                'tags' => $game->tags,
                'image_url' => $game->image_url,
                'normalized_name' => $game->normalized_name,
            ],
        ]);
    }

    public function discover(Request $request)
    {
        $query = Game::query();
        $games = $query->inRandomOrder()->limit(20)->get();
        $games = $games->map(function ($game) {
            return [
                'id' => $game->id,
                'title' => $game->title,
                'name' => $game->name,
                'url' => $game->url,
                'reviews' => $game->reviews,
                'genre' => $game->genre,
                'categoria' => $game->categoria,
                'tags' => $game->tags,
                'image_url' => $game->image_url,
                'normalized_name' => $game->normalized_name,
            ];
        });
        return response()->json(['data' => $games]);
    }

    public function search(Request $request)
    {
        $q = $request->get('q', '');
        $games = Game::where('title', 'like', "%$q%")
            ->orWhere('genre', 'like', "%$q%")
            ->orWhere('categoria', 'like', "%$q%")
            ->paginate(20);
        $games->getCollection()->transform(function ($game) {
            return [
                'id' => $game->id,
                'title' => $game->title,
                'name' => $game->name,
                'url' => $game->url,
                'reviews' => $game->reviews,
                'genre' => $game->genre,
                'categoria' => $game->categoria,
                'tags' => $game->tags,
                'image_url' => $game->image_url,
                'normalized_name' => $game->normalized_name,
            ];
        });
        return response()->json(['data' => $games]);
    }
}
