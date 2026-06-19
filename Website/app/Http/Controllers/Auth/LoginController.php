<?php
namespace App\Http\Controllers\Auth;

use Illuminate\Http\Request;
use Laravel\Socialite\Facades\Socialite;
use App\Http\Controllers\Controller;
use App\Models\User;
use App\Providers\RouteServiceProvider;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Session;


class LoginController extends Controller
{
    public function redirectToKeycloak()
    {
        // Keycloak below v3.2 requires no scopes to be set. 
        // Later versions require the openid scope for all requests.
        // e.g return Socialite::driver('keycloak')->scopes(['openid'])->redirect();
        return Socialite::driver('keycloak')->scopes(['openid'])->redirect();
        
    }

    public function handleKeycloakCallback()
    {
        $user = Socialite::driver('keycloak')->user();
        // this line will be needed if you have an exist Eloquent database User
        // then you can user user data gotten from keycloak to query such table
        // and proceed
        $existingUser = User::where('email', $user['email'])->first();

        if(is_null($existingUser)) {
            $existingUser = User::create([
                'first_name' => $user->user['given_name'],
                'last_name' => $user->user['family_name'],
                'email' => $user->user['email'],
                'phone_number' => '',
                'password' => Hash::make(''),
            ]);
        }

        // Login user
        Auth::login($existingUser);

        // Store session tokens in the database
        $existingUser->session_tokens()->create([
            'session_id' => Session::getId(),
            'id_token' => $user->accessTokenResponseBody['id_token'],
            'access_token' => $user->accessTokenResponseBody['access_token'],
            'refresh_token' => $user->accessTokenResponseBody['refresh_token'],            
        ]);

        return redirect()->intended(RouteServiceProvider::BACKEND);
    }
}