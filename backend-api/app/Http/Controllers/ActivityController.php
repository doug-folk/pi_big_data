<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\Activity;

class ActivityController extends Controller
{
    public function index(Request $request)
    {
        $activities = Activity::with('user')->orderBy('created_at', 'desc')->paginate(20);
        return response()->json(['data' => $activities]);
    }
}
