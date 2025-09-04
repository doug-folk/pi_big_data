<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class FeedController extends Controller
{
    public function index(Request $request)
    {
        $user = $request->user();
        // Exemplo: buscar atividades dos amigos (aqui, apenas atividades do próprio usuário)
        $activities = \App\Models\Activity::where('user_id', $user->id)
            ->orderBy('created_at', 'desc')
            ->limit(50)
            ->get();
        return response()->json($activities);
    }
}
