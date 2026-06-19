<?php

namespace App\Providers;

use Illuminate\Foundation\Support\Providers\EventServiceProvider as ServiceProvider;
use Illuminate\Support\Facades\Event;
use Konekt\Menu\Facades\Menu;

class MenuServiceProvider extends ServiceProvider
{


    /**
     * Register any events for your application.
     */
    public function boot(): void
    {
        $mainMenu = Menu::create('main-menu', ['share' => 'mainMenu']);
        $mainMenu->addItem('home', 'Home', '/');
    }

    /**
     * Determine if events and listeners should be automatically discovered.
     */
    public function shouldDiscoverEvents(): bool
    {
        return false;
    }
}
