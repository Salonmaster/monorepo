<?php

namespace App\Livewire\Auth;

use Livewire\Attributes\Layout;
use Livewire\Component;

class Registered extends Component
{
    #[Layout('auth.components.layout')]
    public function render()
    {
        return view('auth.registered');
    }
}
