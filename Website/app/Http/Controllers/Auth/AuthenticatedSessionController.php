<?php

namespace App\Http\Controllers\Auth;

use Laravel\Socialite\Facades\Socialite;
use App\Http\Controllers\Controller;
use App\Http\Requests\Auth\LoginRequest;
use App\Providers\RouteServiceProvider;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Config;
use Illuminate\View\View;
use App\Models\SessionToken;


class AuthenticatedSessionController extends Controller
{
    /**
     * Display the login view.
     */
    public function create(): View
    {
        return view('auth.login');
    }

    /**
     * Handle an incoming authentication request.
     */
    public function store(LoginRequest $request): RedirectResponse
    {
        $request->authenticate();

        $request->session()->regenerate();

        return redirect()->intended(RouteServiceProvider::BACKEND);
    }

    /**
     * Destroy an authenticated session.
     */
    public function destroy(Request $request): RedirectResponse
    {
        // Fetch tokens for session
        $session_tokens = SessionToken::where('session_id', $request->session()->getId())->first();
        $id_token = '';
        if($session_tokens) {
            $id_token = $session_tokens->id_token;
            $session_tokens->delete();
        }
        Auth::logout();

        $request->session()->invalidate();

        $request->session()->regenerateToken();

        // The URL the user is redirected to after logout.
        $redirectUri = Config::get('app.url');
    
        // Keycloak v18+ does support a post_logout_redirect_uri in combination with a
        // client_id or an id_token_hint parameter or both of them.
        // NOTE: You will need to set valid post logout redirect URI in Keycloak.
        return redirect(Socialite::driver('keycloak')->getLogoutUrl($redirectUri, env('KEYCLOAK_CLIENT_ID'), $id_token));
    }
}
