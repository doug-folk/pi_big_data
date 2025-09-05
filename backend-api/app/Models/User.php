<?php

namespace App\Models;

// use Illuminate\Contracts\Auth\MustVerifyEmail;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Laravel\Sanctum\HasApiTokens;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;

class User extends Authenticatable
{
    use HasApiTokens, HasFactory, Notifiable;

    protected $fillable = [
        'name',
        'email',
        'password',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected function casts(): array
    {
        return [
            'email_verified_at' => 'datetime',
            'password' => 'hashed',
        ];
    }

    // Ratings feitos pelo usuário
    public function ratings()
    {
        return $this->hasMany(Rating::class);
    }

    // Favoritos do usuário
    public function favorites()
    {
        return $this->hasMany(Favorite::class);
    }

    // Conquistas do usuário
    public function achievements()
    {
        return $this->belongsToMany(Achievement::class, 'user_achievements')->withTimestamps()->withPivot('unlocked_at');
    }

    // Atividades do usuário
    public function activities()
    {
        return $this->hasMany(Activity::class);
    }

    // Listas da comunidade criadas pelo usuário
    public function communityLists()
    {
        return $this->hasMany(CommunityList::class);
    }
}
