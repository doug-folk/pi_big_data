<?php

namespace Database\Factories;

use App\Models\CommunityList;
use Illuminate\Database\Eloquent\Factories\Factory;

class CommunityListFactory extends Factory
{
    protected $model = CommunityList::class;

    public function definition(): array
    {
        return [
            'user_id' => \App\Models\User::factory(),
            'title' => $this->faker->sentence(2),
            'description' => $this->faker->sentence(),
        ];
    }
}
