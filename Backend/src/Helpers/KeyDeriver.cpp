// KeyDeriver.cpp
#include "KeyDeriver.h"
#include <openssl/evp.h>
#include <openssl/kdf.h>
#include <stdexcept>

void Helpers::KeyDeriver::deriveKeys(const std::string& masterSecret,
                            std::string& outAesKey,
                            std::string& outHmacKey) {
    const size_t aesLen = 32;
    const size_t hmacLen = 32;
    std::string salt = "drogon-session-salt"; // Optional constant salt

    unsigned char output[aesLen + hmacLen];
    size_t outLen = aesLen + hmacLen;

    EVP_PKEY_CTX* pctx = EVP_PKEY_CTX_new_id(EVP_PKEY_HKDF, nullptr);
    if (!pctx)
        throw std::runtime_error("Failed to create HKDF context");

    if (EVP_PKEY_derive_init(pctx) <= 0 ||
        EVP_PKEY_CTX_set_hkdf_md(pctx, EVP_sha256()) <= 0 ||
        EVP_PKEY_CTX_set1_hkdf_salt(pctx,
            reinterpret_cast<const unsigned char*>(salt.data()), salt.size()) <= 0 ||
        EVP_PKEY_CTX_set1_hkdf_key(pctx,
            reinterpret_cast<const unsigned char*>(masterSecret.data()), masterSecret.size()) <= 0 ||
        EVP_PKEY_CTX_add1_hkdf_info(pctx, nullptr, 0) <= 0 ||
        EVP_PKEY_derive(pctx, output, &outLen) <= 0) {
        EVP_PKEY_CTX_free(pctx);
        throw std::runtime_error("HKDF derivation failed");
    }

    outAesKey.assign(reinterpret_cast<char*>(output), aesLen);
    outHmacKey.assign(reinterpret_cast<char*>(output + aesLen), hmacLen);

    EVP_PKEY_CTX_free(pctx);
}
