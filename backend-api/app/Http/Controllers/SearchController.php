<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class SearchController extends Controller
{
    public function advanced(Request $request)
    {
        $query = \App\Models\Game::query();
        if ($request->filled('title')) {
            $query->where('title', 'like', '%' . $request->title . '%');
        }
        if ($request->filled('genre')) {
            $query->where('genre', 'like', '%' . $request->genre . '%');
        }
        if ($request->filled('platform')) {
            $query->where('platform', 'like', '%' . $request->platform . '%');
        }
        if ($request->filled('release_year')) {
            $query->whereYear('release_date', $request->release_year);
        }
        $games = $query->paginate(20);
        return response()->json($games);
    }
}
