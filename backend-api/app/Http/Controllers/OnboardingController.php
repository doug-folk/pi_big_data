<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;

class OnboardingController extends Controller
{
    public function preferences(Request $request)
    {
        $data = $request->validate([
            'genres' => 'array',
            'genres.*' => 'string',
            'platforms' => 'array',
            'platforms.*' => 'string',
        ]);
        $user = $request->user();
        // Exemplo: salvar preferências como json em um campo do usuário
        $user->preferences = [
            'genres' => $data['genres'] ?? [],
            'platforms' => $data['platforms'] ?? [],
        ];
        $user->save();
        return response()->json(['message' => 'Preferências salvas com sucesso']);
    }
}
