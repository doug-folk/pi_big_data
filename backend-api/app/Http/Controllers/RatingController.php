<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Rating;
use App\Models\Game;

class RatingController extends Controller
{
    public function index($game_id)
    {
        $ratings = Rating::where('game_id', $game_id)->with('user')->get();
    return response()->json(['data' => $ratings]);
    }

    public function store(Request $request, $game_id)
    {
        $data = $request->validate([
            'rating' => 'required|integer|min:1|max:5',
            'comment' => 'nullable|string|max:1000',
        ]);
        $rating = Rating::updateOrCreate(
            [
                'user_id' => $request->user()->id,
                'game_id' => $game_id,
            ],
            [
                'rating' => $data['rating'],
                'comment' => $data['comment'] ?? null,
            ]
        );
    return response()->json(['rating' => $rating], 201);
    }

    public function update(Request $request, $game_id)
    {
        $data = $request->validate([
            'rating' => 'required|integer|min:1|max:5',
            'comment' => 'nullable|string|max:1000',
        ]);
        $rating = Rating::where('user_id', $request->user()->id)
            ->where('game_id', $game_id)
            ->firstOrFail();
        $rating->rating = $data['rating'];
        $rating->comment = $data['comment'] ?? null;
        $rating->save();
        return response()->json(['rating' => $rating], 200);
    }

    public function destroy($id)
    {
        $rating = Rating::findOrFail($id);
        if ($rating->user_id !== auth()->id()) {
            return response()->json(['message' => 'Não autorizado'], 403);
        }
        $rating->delete();
        return response()->json(['message' => 'Avaliação removida']);
    }
}
