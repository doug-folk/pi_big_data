<?php

namespace Database\Factories;

use App\Models\Game;
use Illuminate\Database\Eloquent\Factories\Factory;

class GameFactory extends Factory
{
    protected $model = Game::class;

    public function definition(): array
    {
        return [
                'title' => $this->faker->sentence(3),
                'description' => $this->faker->paragraph(),
                'genre' => $this->faker->word(),
                'tags' => implode(',', $this->faker->words(3)),
                'platform' => $this->faker->randomElement(['PC', 'PlayStation', 'Xbox', 'Switch']),
                'developer' => $this->faker->company(),
                'publisher' => $this->faker->company(),
                'release_date' => $this->faker->date(),
        ];
    }
}
