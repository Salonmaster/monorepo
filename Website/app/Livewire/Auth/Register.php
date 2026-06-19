<?php

namespace App\Livewire\Auth;

use App\Models\User;
use Illuminate\Auth\Events\Registered;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Livewire\Attributes\Layout;
use Livewire\Attributes\Rule;
use Livewire\Component;

class Register extends Component
{
    #[Rule(['required', 'string', 'max:255'])]
    public $first_name = '';

    #[Rule(['required', 'string', 'max:255'])]
    public $last_name = '';

    #[Rule(['required', 'string', 'email', 'max:255', 'unique:'.User::class])]
    public $email = '';

    #[Rule('required')]
    public $phone_number = '';

    #[Rule(['required', 'confirmed'])]
    public $password = '';

    public $password_confirmation = '';

    #[Rule(['required', 'boolean', 'accepted'])]
    public $accept_agreement = false;

    #[Layout('auth.components.layout')]
    public function register()
    {
        $this->validate();

        // Create user
        $user = User::create([
            'first_name' => $this->first_name,
            'last_name' => $this->last_name,
            'email' => $this->email,
            'phone_number' => $this->phone_number,
            'password' => Hash::make($this->password),
        ]);

        event(new Registered($user));
        Auth::loginUsingId($user->id);

        return $this->redirect(route('registered'), navigate: true);
    }

    public function render()
    {
        return view('auth.register');
    }
}
