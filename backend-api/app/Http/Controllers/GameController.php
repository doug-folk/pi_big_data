<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Game;

class GameController extends Controller
{
    public function index(Request $request)
    {
        // Filtro básico: gênero, categoria, busca, tags, paginação
        $query = Game::query();
        if ($request->has('genre')) {
            $query->where('genre', 'like', '%' . $request->genre . '%');
        }
        if ($request->has('categoria')) {
            $query->where('categoria', 'like', '%' . $request->categoria . '%');
        }
        if ($request->has('tags')) {
            $tags = is_array($request->tags) ? $request->tags : explode(',', $request->tags);
            foreach ($tags as $tag) {
                $query->whereJsonContains('tags', $tag);
            }
        }
        if ($request->has('q')) {
            $query->where(function($q) use ($request) {
                $q->where('title', 'like', '%' . $request->q . '%')
                  ->orWhere('genre', 'like', '%' . $request->q . '%')
                  ->orWhere('categoria', 'like', '%' . $request->q . '%');
            });
        }
        $games = $query->paginate(20);
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
