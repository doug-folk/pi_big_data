<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class Game extends Model
{
    use HasFactory;

    protected $fillable = [
        'title',
        'description',
        'genre',
        'tags',
        'platform',
        'developer',
        'publisher',
        'release_date',
    ];

    // Ratings recebidos para este jogo
    public function ratings()
    {
        return $this->hasMany(Rating::class);
    }

    // Favoritos deste jogo
    public function favorites()
    {
        return $this->hasMany(Favorite::class);
    }

    // Listas da comunidade que incluem este jogo
    public function communityLists()
    {
        return $this->belongsToMany(CommunityList::class, 'community_list_games');
    }
}
