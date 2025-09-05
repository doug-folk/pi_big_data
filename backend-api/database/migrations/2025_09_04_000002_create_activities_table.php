<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('activities', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->onDelete('cascade');
            $table->foreignId('game_id')->nullable()->constrained()->onDelete('cascade');
            $table->string('type'); // ex: rating, favorite, achievement, etc
            $table->unsignedBigInteger('related_id')->nullable(); // id relacionado (rating_id, achievement_id, etc)
            $table->string('related_type')->nullable(); // tipo relacionado
            $table->text('description')->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('activities');
    }
};
