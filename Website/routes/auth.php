<?php

use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Auth\LoginController;
use Illuminate\Support\Facades\Route;

Route::middleware('login')->group(function () {
    Route::get('keycloak', [LoginController::class, 'redirectToKeycloak'])->name('login');
    Route::get('keycloak/callback', [LoginController::class, 'handleKeycloakCallback']);
    Route::get('logout', [AuthenticatedSessionController::class, 'destroy'])
        ->name('logout');
});
