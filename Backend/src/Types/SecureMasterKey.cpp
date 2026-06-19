// SecureMasterKey.cpp
#include "SecureMasterKey.h"
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <cstring>
#include <stdexcept>

Types::SecureMasterKey::SecureMasterKey(const std::string& rawKey) {
    iv_.resize(16);
    RAND_bytes(iv_.data(), iv_.size());
    encryptInMemory(rawKey);
}

Types::SecureMasterKey::~SecureMasterKey() {
    clearSensitive(encrypted_);
    clearSensitive(iv_);
    clearSensitive(tempKey_);
}

void Types::SecureMasterKey::clearSensitive(std::vector<unsigned char>& vec) {
    std::fill(vec.begin(), vec.end(), 0);
    vec.clear();
    vec.shrink_to_fit();
}

void Types::SecureMasterKey::encryptInMemory(const std::string& plain) {
    encrypted_.resize(plain.size());
    tempKey_.resize(32);
    RAND_bytes(tempKey_.data(), tempKey_.size());

    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(ctx, EVP_aes_256_ctr(), nullptr, tempKey_.data(), iv_.data());

    int len;
    EVP_EncryptUpdate(ctx, encrypted_.data(), &len,
                      reinterpret_cast<const unsigned char*>(plain.data()), plain.size());
    EVP_EncryptFinal_ex(ctx, encrypted_.data() + len, &len);

    EVP_CIPHER_CTX_free(ctx);
}

std::string Types::SecureMasterKey::unlock() {
    std::vector<unsigned char> plain(encrypted_.size());
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    EVP_DecryptInit_ex(ctx, EVP_aes_256_ctr(), nullptr, tempKey_.data(), iv_.data());

    int len;
    EVP_DecryptUpdate(ctx, plain.data(), &len, encrypted_.data(), encrypted_.size());
    EVP_DecryptFinal_ex(ctx, plain.data() + len, &len);
    EVP_CIPHER_CTX_free(ctx);

    return std::string(reinterpret_cast<char*>(plain.data()), plain.size());
}