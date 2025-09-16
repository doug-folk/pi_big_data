<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use App\Models\Game;

class GameController extends Controller
{
    public function index(Request $request)
    {
        $games = Game::all();
        return response()->json(['data' => $games]);
    }

    public function show($id)
    {
        $game = Game::findOrFail($id);
        return response()->json(['game' => $game]);
    }

    public function discover(Request $request)
    {
        $games = Game::inRandomOrder()->limit(20)->get();
        return response()->json(['data' => $games]);
    }

    public function search(Request $request)
    {
        $q = $request->get('q', '');
        $games = Game::where('title', 'like', "%$q%")
            ->orWhere('genre', 'like', "%$q%")
            ->orWhere('categoria', 'like', "%$q%")
            ->paginate(20);

        return response()->json(['data' => $games]);
    }

    public function recommendByMood(Request $request)
    {
        $mood = $request->get('mood', 'Unknown');
        $top_n = $request->get('top_n', 10);

        $response = Http::get('http://127.0.0.1:8001/recommendations/by-mood', [
            'mood' => $mood,
            'top_n' => $top_n
        ]);

        $ids = collect($response->json())->pluck('id')->toArray();
        $games = Game::whereIn('id', $ids)->get();

        return response()->json(['data' => $games]);
    }

    public function recommendForGame($game_id, Request $request)
    {
        $top_n = $request->get('top_n', 10);

        $response = Http::get("http://127.0.0.1:8001/recommendations/for-game/{$game_id}", [
            'top_n' => $top_n
        ]);

        $ids = collect($response->json())->pluck('id')->toArray();
        $games = Game::whereIn('id', $ids)->get();

        return response()->json(['data' => $games]);
    }

    public function discoverByFilter(Request $request)
    {
        $params = $request->only(['genre', 'categoria', 'tag', 'top_n']);

        $response = Http::get('http://127.0.0.1:8001/discover/by-filter', $params);

        $ids = collect($response->json())->pluck('id')->toArray();
        $games = Game::whereIn('id', $ids)->inRandomOrder()->get();

        return response()->json(['data' => $games]);
    }

    public function discoverRandom(Request $request)
    {
        $params = $request->only(['genre', 'categoria', 'tag', 'n']);

        $response = Http::get('http://127.0.0.1:8001/discover/random', $params);

        $ids = collect($response->json())->pluck('id')->toArray();
        $games = Game::whereIn('id', $ids)->get();

        return response()->json(['data' => $games]);
    }

    public function discoverByCluster($game_id, Request $request)
    {
        $top_n = $request->get('top_n', 10);

        $response = Http::get("http://127.0.0.1:8001/discover/by-cluster/{$game_id}", [
            'top_n' => $top_n
        ]);

        $ids = collect($response->json())->pluck('id')->toArray();
        $games = Game::whereIn('id', $ids)->get();

        return response()->json(['data' => $games]);
    }
}
