<?php

namespace App\Livewire\Auth;

use Illuminate\Support\Facades\Password;
use Livewire\Attributes\Layout;
use Livewire\Attributes\Rule;
use Livewire\Component;

class ForgotPassword extends Component
{
    #[Rule('required|email')]
    public $email;

    public $failed = false;
    public $succeeded = false;

    #[Layout('auth.components.layout')]
    public function render()
    {
        return view('auth.forgot-password');
    }

    public function submit()
    {
        // Validate input and check if request is not throttled
        $this->validate();

        // We will send the password reset link to this user. Once we have attempted
        // to send the link, we will examine the response then see the message we
        // need to show to the user. Finally, we'll send out a proper response.
        $status = Password::sendResetLink(
            $this->only('email')
        );

        $this->failed = $status != Password::RESET_LINK_SENT;
        $this->succeeded = $status == Password::RESET_LINK_SENT;
    }
}
