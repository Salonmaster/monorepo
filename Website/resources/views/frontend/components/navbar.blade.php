<nav class="navbar navbar-marketing navbar-expand-lg bg-white navbar-light">
    <div class="container px-5">
        <a class="navbar-brand text-primary" href="{{ route('home') }}">{{ config('app.name') }}</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
            aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation"><i
                data-feather="menu"></i></button>
        <div class="collapse navbar-collapse" id="navbarSupportedContent">
            <ul class="navbar-nav ms-auto me-lg-5">
                @foreach ($mainMenu->items as $item)
                    <li class="nav-item"><a class="nav-link" href="{{ $item->url }}">{{ $item->title }}</a></li>
                @endforeach
            </ul>
            @guest
            <a class="btn fw-500 ms-lg-4 btn-primary" href="{{ route('login') }}">
                Login
                <i class="ms-2" data-feather="arrow-right"></i>
            </a>
            @endguest
            @auth
            <a class="btn fw-500 ms-lg-4 btn-primary" href="{{ route('backend') }}">
                Mijn account
                <i class="ms-2" data-feather="arrow-right"></i>
            </a>
            @endauth
        </div>
    </div>
</nav>
