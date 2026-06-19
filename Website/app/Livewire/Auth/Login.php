<?php

namespace App\Livewire\Auth;

use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\RateLimiter;
use Illuminate\Support\Str;
use Livewire\Attributes\Layout;
use Livewire\Attributes\Rule;
use Livewire\Component;

class Login extends Component
{
    public $invalid = false;

    public $error_message = '';

    #[Rule('required|email')]
    public $email = '';

    #[Rule('required|min:7')]
    public $password = '';

    public $remember = true;

    #[Layout('auth.components.layout')]
    public function login()
    {
        Log::warning('JOJOJOJOJ');
        // Validate input and check if request is not throttled
        $this->validate();
        if (RateLimiter::tooManyAttempts($this->throttleKey(), 5)) {
            $this->error_message = 'Teveel pogingen probeer het opnieuw over: '.RateLimiter::availableIn($this->throttleKey()).' seconden.';
            $this->invalid = true;

            return;
        }
        // Hit rate limiter and attempt to authenticate
        if (Auth::attempt($this->only('email', 'password'), $this->remember)) {

        } else {
            RateLimiter::hit($this->throttleKey());
            $this->error_message = 'Kan niet inloggen, controleer uw inloggegevens';
            $this->invalid = true;
        }

    }

    public function throttleKey(): string
    {
        return Str::transliterate(Str::lower($this->email));
    }

    public function render()
    {
        return view('auth.login');
    }
}
