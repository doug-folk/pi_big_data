<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Illuminate\Http\Client\PendingRequest;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use App\Models\Game;
use Illuminate\Support\Collection;

class GameController extends Controller
{
    public function index(Request $request)
    {
        $games = Game::query()->get();

        return response()->json(['data' => $games]);
    }

    public function show($id)
    {
        $game = Game::findOrFail($id);
        return response()->json(['game' => $game]);
    }

    public function discover(Request $request)
    {
        $games = Game::inRandomOrder()->limit(20)->get();
        return response()->json(['data' => $games]);
    }

    public function search(Request $request)
    {
        $q = $request->get('q', '');
        $games = Game::where('title', 'like', "%$q%")
            ->orWhere('genre', 'like', "%$q%")
            ->orWhere('categoria', 'like', "%$q%")
            ->paginate(20);

        return response()->json(['data' => $games]);
    }

    public function recommendByMood(Request $request)
    {
        $mood = $request->get('mood', 'Unknown');
        $top_n = (int) $request->get('top_n', 10);

        try {
            $response = $this->recommender()->get('/recommendations/by-mood', [
                'mood' => $mood,
                'top_n' => $top_n,
            ]);

            $response->throw();

            $ids = $this->extractIds($response->json());
            $games = $this->hydrateGames($ids);

            if ($games->isNotEmpty()) {
                return response()->json(['data' => $games]);
            }
        } catch (\Throwable $e) {
            Log::warning('Fallback recommendByMood', [
                'mood' => $mood,
                'top_n' => $top_n,
                'error' => $e->getMessage(),
            ]);
        }

        $games = Game::query()
            ->where(function ($query) use ($mood) {
                $query->where('genre', 'like', "%{$mood}%")
                    ->orWhere('tags', 'like', "%{$mood}%")
                    ->orWhere('categoria', 'like', "%{$mood}%");
            })
            ->inRandomOrder()
            ->limit(max($top_n, 1))
            ->get();

        if ($games->isEmpty()) {
            $games = $this->fallbackRandomGames(max($top_n, 1));
        }

        return response()->json(['data' => $games]);
    }

    public function recommendForGame($game_id, Request $request)
    {
        $top_n = (int) $request->get('top_n', 10);

        try {
            $response = $this->recommender()->get("/recommendations/for-game/{$game_id}", [
                'top_n' => $top_n,
            ]);

            $response->throw();

            $ids = $this->extractIds($response->json());
            $games = $this->hydrateGames($ids);

            if ($games->isNotEmpty()) {
                return response()->json(['data' => $games]);
            }
        } catch (\Throwable $e) {
            Log::warning('Fallback recommendForGame', [
                'game_id' => $game_id,
                'top_n' => $top_n,
                'error' => $e->getMessage(),
            ]);
        }

        $reference = Game::find($game_id);
        $fallback = Game::query();

        if ($reference) {
            $fallback->where('id', '!=', $reference->id)
                ->where(function ($query) use ($reference) {
                    $hasCondition = false;

                    if (!empty($reference->genre)) {
                        $query->orWhere('genre', 'like', "%{$reference->genre}%");
                        $hasCondition = true;
                    }

                    if (!empty($reference->categoria)) {
                        $query->orWhere('categoria', 'like', "%{$reference->categoria}%");
                        $hasCondition = true;
                    }

                    if (!empty($reference->tags)) {
                        $query->orWhere('tags', 'like', "%{$reference->tags}%");
                        $hasCondition = true;
                    }

                    if (!$hasCondition) {
                        $query->orWhereNotNull('id');
                    }
                });
        }

        $games = $fallback->inRandomOrder()
            ->limit(max($top_n, 1))
            ->get();

        if ($games->isEmpty()) {
            $games = $this->fallbackRandomGames(max($top_n, 1));
        }

        return response()->json(['data' => $games]);
    }

    public function discoverByFilter(Request $request)
    {
        $params = $request->only(['genre', 'categoria', 'tag', 'top_n']);

        try {
            $response = $this->recommender()->get('/discover/by-filter', $params);

            $response->throw();

            $ids = $this->extractIds($response->json());
            $games = $this->hydrateGames($ids);

            if ($games->isNotEmpty()) {
                return response()->json(['data' => $games]);
            }
        } catch (\Throwable $e) {
            Log::warning('Fallback discoverByFilter', [
                'params' => $params,
                'error' => $e->getMessage(),
            ]);
        }

        $fallback = Game::query();

        if (!empty($params['genre'])) {
            $fallback->where('genre', 'like', '%' . $params['genre'] . '%');
        }

        if (!empty($params['categoria'])) {
            $fallback->where('categoria', 'like', '%' . $params['categoria'] . '%');
        }

        if (!empty($params['tag'])) {
            $fallback->where('tags', 'like', '%' . $params['tag'] . '%');
        }

        $top_n = isset($params['top_n']) ? (int) $params['top_n'] : 20;

        $games = $fallback->inRandomOrder()
            ->limit(max($top_n, 1))
            ->get();

        if ($games->isEmpty()) {
            $games = $this->fallbackRandomGames(max($top_n, 1));
        }

        return response()->json(['data' => $games]);
    }

    public function discoverRandom(Request $request)
    {
        $params = $request->only(['genre', 'categoria', 'tag', 'n']);

        try {
            $response = $this->recommender()->get('/discover/random', $params);

            $response->throw();

            $ids = $this->extractIds($response->json());
            $games = $this->hydrateGames($ids);

            if ($games->isNotEmpty()) {
                return response()->json(['data' => $games]);
            }
        } catch (\Throwable $e) {
            Log::warning('Fallback discoverRandom', [
                'params' => $params,
                'error' => $e->getMessage(),
            ]);
        }

        $n = isset($params['n']) ? (int) $params['n'] : 5;
        $n = max($n, 1);

        $games = $this->fallbackRandomGames($n);

        return response()->json(['data' => $games]);
    }

    public function discoverByCluster($game_id, Request $request)
    {
        $top_n = (int) $request->get('top_n', 10);

        try {
            $response = $this->recommender()->get("/discover/by-cluster/{$game_id}", [
                'top_n' => $top_n,
            ]);

            $response->throw();

            $payload = $response->json();
            $recommendations = is_array($payload) ? ($payload['recommendations'] ?? []) : [];
            $ids = $this->extractIds(is_array($recommendations) ? $recommendations : []);
            $games = $this->hydrateGames($ids);
            $clusterInfo = is_array($payload) ? ($payload['cluster_info'] ?? null) : null;

            if ($games->isNotEmpty()) {
                return response()->json([
                    'data' => $games,
                    'cluster_info' => $clusterInfo,
                ]);
            }
        } catch (\Throwable $e) {
            Log::warning('Fallback discoverByCluster', [
                'game_id' => $game_id,
                'top_n' => $top_n,
                'error' => $e->getMessage(),
            ]);
        }

        $games = $this->fallbackRandomGames(max($top_n, 1));

        return response()->json([
            'data' => $games,
            'cluster_info' => null,
        ]);
    }

    protected function recommender(): PendingRequest
    {
        $baseUrl = rtrim(config('services.recommender.url', 'http://127.0.0.1:8001'), '/');

        return Http::baseUrl($baseUrl);
    }

    /**
     * @param array<int|string, mixed> $payload
     * @return array<int>
     */
    protected function extractIds(array $payload): array
    {
        return collect($payload)
            ->pluck('id')
            ->filter(function ($id) {
                return !is_null($id);
            })
            ->map(function ($id) {
                return (int) $id;
            })
            ->unique()
            ->values()
            ->all();
    }

    /**
     * @param array<int> $ids
     */
    protected function hydrateGames(array $ids): Collection
    {
        if (empty($ids)) {
            return collect();
        }

        $games = Game::whereIn('id', $ids)->get()->keyBy('id');

        return collect($ids)
            ->map(function ($id) use ($games) {
                return $games->get($id);
            })
            ->filter()
            ->values();
    }

    protected function fallbackRandomGames(int $limit): Collection
    {
        return Game::query()
            ->inRandomOrder()
            ->limit(max($limit, 1))
            ->get();
    }
}
