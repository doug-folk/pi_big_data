<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class CommunityController extends Controller
{
    public function index()
    {
        $lists = \App\Models\CommunityList::with('user', 'games')->paginate(20);
        return response()->json($lists);
    }

    public function show($id)
    {
        $list = \App\Models\CommunityList::with('user', 'games')->findOrFail($id);
        return response()->json($list);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'title' => 'required|string|max:255',
            'description' => 'nullable|string',
            'games' => 'array',
            'games.*' => 'integer|exists:games,id',
        ]);
        $list = \App\Models\CommunityList::create([
            'user_id' => $request->user()->id,
            'title' => $data['title'],
            'description' => $data['description'] ?? null,
        ]);
        if (!empty($data['games'])) {
            $list->games()->sync($data['games']);
        }
        return response()->json($list, 201);
    }
}
