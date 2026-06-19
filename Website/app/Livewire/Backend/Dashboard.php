<?php

namespace App\Livewire\Backend;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Livewire\Component;

class Dashboard extends Component
{
    public $title = 'Register';

    public $user;

    public function mount(Request $request)
    {
        $this->user = $request->user();
    }

    public function render()
    {
        $user = Auth::user();

        return view('backend.dashboard')->layout('backend.components.layout', compact('user'));
    }
}
