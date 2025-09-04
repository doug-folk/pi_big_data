<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Game;

class GameController extends Controller
{
    public function index(Request $request)
    {
        // Filtros: gênero, plataforma, busca, paginação
        $query = Game::query();
        if ($request->has('genre')) {
            $query->where('genre', 'like', '%' . $request->genre . '%');
        }
        if ($request->has('platform')) {
            $query->where('platform', 'like', '%' . $request->platform . '%');
        }
        if ($request->has('q')) {
            $query->where('title', 'like', '%' . $request->q . '%');
        }
        $games = $query->paginate(20);
        return response()->json($games);
    }

    public function show($id)
    {
        $game = Game::with(['ratings.user', 'favorites', 'comments'])->findOrFail($id);
        // Média, número de avaliações, comentários, link
        $avg = $game->ratings()->avg('rating');
        $count = $game->ratings()->count();
        return response()->json([
            'game' => $game,
            'average_rating' => $avg,
            'ratings_count' => $count,
            'comments' => $game->ratings()->with('user')->get(),
            'link' => $game->link,
        ]);
    }

    public function discover(Request $request)
    {
        // Exemplo: jogos populares, recentes, aleatórios, por gênero
        $type = $request->get('type', 'popular');
        $query = Game::query();
        if ($type === 'random') {
            $games = $query->inRandomOrder()->limit(20)->get();
        } elseif ($type === 'recent') {
            $games = $query->orderBy('release_date', 'desc')->limit(20)->get();
        } else {
            $games = $query->orderBy('ratings_count', 'desc')->limit(20)->get();
        }
        return response()->json($games);
    }

    public function search(Request $request)
    {
        $q = $request->get('q', '');
        $games = Game::where('title', 'like', "%$q%")
            ->orWhere('genre', 'like', "%$q%")
            ->orWhere('platform', 'like', "%$q%")
            ->paginate(20);
        return response()->json($games);
    }
}
