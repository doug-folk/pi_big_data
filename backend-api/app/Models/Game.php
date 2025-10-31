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

    protected function normalizeUrl(?string $value): ?string
    {
        if (!is_string($value)) {
            return null;
        }

        $trimmed = trim($value);

        if ($trimmed === '' || strcasecmp($trimmed, 'unknown') === 0) {
            return null;
        }

        return preg_match('/^https?:\/\//i', $trimmed) ? $trimmed : null;
    }

    public function getUrlAttribute($value): ?string
    {
        return $this->normalizeUrl($value);
    }

    public function getImageUrlAttribute($value): ?string
    {
        return $this->normalizeUrl($value);
    }
}
