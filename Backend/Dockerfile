FROM alpine:3.21 AS builder

RUN apk add --no-cache \
    build-base \
    cmake \
    git \
    python3 \
    py3-pip \
    py3-numpy \
    libuv-dev \
    openssl-dev \
    zlib-dev \
    linux-headers \
    perl-utils \
    boost-dev \
    upx

# Conan setup
RUN python3 -m venv /venv && \
    /venv/bin/pip install --no-cache-dir conan

WORKDIR /app

COPY conanfile.py conanfile.py

# Configure Conan to use musl-compatible dynamic build
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        CONAN_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        CONAN_ARCH="armv8"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    GCC_VER=$(gcc -dumpversion | cut -d. -f1) && \
    /venv/bin/conan profile detect --force && \
    printf "[settings]\n\
os=Linux\n\
arch=%s\n\
compiler=gcc\n\
compiler.version=%s\n\
compiler.libcxx=libstdc++11\n\
compiler.cppstd=23\n\
build_type=Release\n\
[options]\n\
*:shared=False\n" "$CONAN_ARCH" "$GCC_VER" > ~/.conan2/profiles/default

RUN /venv/bin/conan install . --build=missing -s build_type=Release -v status

COPY . .

# Build your project
RUN /venv/bin/conan build . --build=missing -s build_type=Release -v status

# Strip the binary to reduce size
RUN strip --strip-unneeded build/Release/Backend && \
    upx --lzma build/Release/Backend

# Create a Conan profile for the build environment
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Runtime stage: Alpine!
FROM scratch
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group
COPY --from=builder /app/build/Release/Backend /app/Backend

USER appuser

ENTRYPOINT ["/app/Backend", "--config", "/app/config.json"]
