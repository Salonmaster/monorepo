<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

class SessionToken extends Model
{
    use HasFactory;

    protected $fillable = [
        'session_id',
        'id_token',
        'access_token',
        'refresh_token',
    ];

    public function user() {
        return $this->hasOne(User::class);
    }

}
