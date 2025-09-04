<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class RecommendationController extends Controller
{
    public function user($user_id)
    {
        // Exemplo de chamada real (mock):
        // $response = Http::get('http://localhost:8001/recommendations/for-user/'.$user_id);
        // return $response->json();
        return response()->json([
            'user_id' => $user_id,
            'recommendations' => ['game_id_1', 'game_id_2', 'game_id_3'],
        ]);
    }

    public function game($game_id)
    {
        return response()->json([
            'game_id' => $game_id,
            'recommendations' => ['game_id_4', 'game_id_5'],
        ]);
    }

    public function mood(Request $request)
    {
        $mood = $request->get('mood', 'relaxar');
        return response()->json([
            'mood' => $mood,
            'recommendations' => ['game_id_6', 'game_id_7'],
        ]);
    }

    public function forgotten()
    {
        return response()->json([
            'recommendations' => ['game_id_8', 'game_id_9'],
        ]);
    }
}
