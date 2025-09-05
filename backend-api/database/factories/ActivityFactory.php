<?php

namespace Database\Factories;

use App\Models\Activity;
use Illuminate\Database\Eloquent\Factories\Factory;

class ActivityFactory extends Factory
{
    protected $model = Activity::class;

    public function definition(): array
    {
        return [
            'user_id' => \App\Models\User::factory(),
            'type' => $this->faker->randomElement(['rating', 'favorite', 'achievement']),
            'related_id' => null,
            'related_type' => null,
            'description' => $this->faker->sentence(),
        ];
    }
}
