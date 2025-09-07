<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Game extends Model
{
    use HasFactory;

    protected $fillable = [
        'id',
        'title',
        'name',
        'url',
        'reviews',
        'genre',
        'categoria',
        'tags',
        'image_url',
        'normalized_name',
    ];

    protected $casts = [
        'tags' => 'array',
    ];
}
