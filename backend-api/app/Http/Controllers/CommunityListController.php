<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\CommunityList;
use App\Models\Game;
use Illuminate\Support\Facades\Auth;

class CommunityListController extends Controller
{
    // GET /community/lists
    public function index()
    {
        $lists = CommunityList::with('games', 'user')->get();
        return response()->json(['community_lists' => $lists]);
    }

    // POST /community/lists
    public function store(Request $request)
    {
        $request->validate([
            'title' => 'required|string|max:255',
            'description' => 'nullable|string',
        ]);
        $list = CommunityList::create([
            'user_id' => Auth::id(),
            'title' => $request->title,
            'description' => $request->description,
        ]);
        return response()->json(['community_list' => $list], 201);
    }

    // POST /community/lists/{id}/vote
    public function vote($id)
    {
        // Implementação fictícia: incrementa um campo de votos
        $list = CommunityList::findOrFail($id);
        $list->votes = ($list->votes ?? 0) + 1;
        $list->save();
        return response()->json(['community_list' => $list]);
    }

    // POST /community-lists/{id}/games
    public function addGame(Request $request, $id)
    {
        $request->validate([
            'game_id' => 'required|exists:games,id',
        ]);
        $list = CommunityList::findOrFail($id);
        $list->games()->attach($request->game_id);
        return response()->json(['community_list' => $list->load('games')], 201);
    }
}
