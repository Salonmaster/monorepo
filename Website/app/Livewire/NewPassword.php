<?php

namespace App\Livewire;

use Livewire\Component;

class NewPassword extends Component
{
    public $email;

    public function render()
    {
        return view('livewire.new-password');
    }
}
