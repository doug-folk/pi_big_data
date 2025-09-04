<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class AchievementController extends Controller
{
    public function index(Request $request)
    {
        $user = $request->user();
        $achievements = $user->achievements()->withPivot('unlocked_at')->get();
        return response()->json($achievements);
    }

    public function store(Request $request)
    {
        $data = $request->validate([
            'achievement_id' => 'required|exists:achievements,id',
        ]);
        $user = $request->user();
        $user->achievements()->syncWithoutDetaching([
            $data['achievement_id'] => ['unlocked_at' => now()]
        ]);
        return response()->json(['message' => 'Conquista registrada com sucesso']);
    }
}
