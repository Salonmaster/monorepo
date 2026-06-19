// SessionCrypto.cpp
#include "SessionCrypto.h"
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <openssl/hmac.h>
#include <drogon/utils/Utilities.h>
#include <stdexcept>
#include <vector>
#include <cstring>

Helpers::SessionCrypto::SessionCrypto(const std::string& aesKey, const std::string& hmacKey)
    : aesKey_(aesKey), hmacKey_(hmacKey) {
    if (aesKey.size() != 32)
        throw std::invalid_argument("AES key must be 32 bytes (256-bit)");
    if (hmacKey.size() < 32)
        throw std::invalid_argument("HMAC key must be at least 32 bytes");
}

Helpers::SessionCrypto::~SessionCrypto() {
    // Clear sensitive keys
    std::memset(aesKey_.data(), 0, aesKey_.size());
    std::memset(hmacKey_.data(), 0, hmacKey_.size());
}

std::string Helpers::SessionCrypto::encryptAndSign(const std::string& sessionId) {
    std::vector<unsigned char> iv(IV_LENGTH);
    RAND_bytes(iv.data(), IV_LENGTH);

    std::vector<unsigned char> ciphertext(sessionId.size());
    std::vector<unsigned char> tag(TAG_LENGTH);

    // AES-GCM Encryption
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    EVP_EncryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr);
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, IV_LENGTH, nullptr);
    EVP_EncryptInit_ex(ctx, nullptr, nullptr,
                       reinterpret_cast<const unsigned char*>(aesKey_.data()),
                       iv.data());

    int len;
    EVP_EncryptUpdate(ctx, ciphertext.data(), &len,
                      reinterpret_cast<const unsigned char*>(sessionId.data()),
                      sessionId.size());
    int ciphertext_len = len;

    EVP_EncryptFinal_ex(ctx, ciphertext.data() + len, &len);
    ciphertext_len += len;

    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, TAG_LENGTH, tag.data());
    EVP_CIPHER_CTX_free(ctx);

    // Combine IV + ciphertext + tag
    std::string payload(reinterpret_cast<char*>(iv.data()), IV_LENGTH);
    payload.append(reinterpret_cast<char*>(ciphertext.data()), ciphertext_len);
    payload.append(reinterpret_cast<char*>(tag.data()), TAG_LENGTH);

    // HMAC-SHA256 Signing
    unsigned char hmac[EVP_MAX_MD_SIZE];
    unsigned int hmacLen;
    HMAC(EVP_sha256(), hmacKey_.data(), hmacKey_.size(),
         reinterpret_cast<const unsigned char*>(payload.data()), payload.size(),
         hmac, &hmacLen);

    payload.append(reinterpret_cast<char*>(hmac), HMAC_LENGTH);

    return drogon::utils::base64Encode(payload);
}

std::string Helpers::SessionCrypto::decryptAndVerify(const std::string& tokenBase64) {
    std::string raw = drogon::utils::base64Decode(tokenBase64);
    if (raw.size() < IV_LENGTH + TAG_LENGTH + HMAC_LENGTH)
        throw std::runtime_error("Token too short");

    size_t cipherLen = raw.size() - IV_LENGTH - TAG_LENGTH - HMAC_LENGTH;
    const unsigned char* iv = reinterpret_cast<const unsigned char*>(raw.data());
    const unsigned char* ciphertext = iv + IV_LENGTH;
    const unsigned char* tag = ciphertext + cipherLen;
    const unsigned char* hmac = tag + TAG_LENGTH;

    // Verify HMAC
    std::string payload(raw.data(), raw.size() - HMAC_LENGTH);
    unsigned char expectedHmac[EVP_MAX_MD_SIZE];
    unsigned int hmacLen;
    HMAC(EVP_sha256(), hmacKey_.data(), hmacKey_.size(),
         reinterpret_cast<const unsigned char*>(payload.data()), payload.size(),
         expectedHmac, &hmacLen);

    if (CRYPTO_memcmp(hmac, expectedHmac, HMAC_LENGTH) != 0)
        throw std::runtime_error("Invalid token: HMAC verification failed");

    std::vector<unsigned char> decrypted(cipherLen);
    EVP_CIPHER_CTX* ctx = EVP_CIPHER_CTX_new();
    EVP_DecryptInit_ex(ctx, EVP_aes_256_gcm(), nullptr, nullptr, nullptr);
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, IV_LENGTH, nullptr);
    EVP_DecryptInit_ex(ctx, nullptr, nullptr,
                       reinterpret_cast<const unsigned char*>(aesKey_.data()),
                       iv);

    int len;
    EVP_DecryptUpdate(ctx, decrypted.data(), &len, ciphertext, cipherLen);
    EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, TAG_LENGTH, const_cast<unsigned char*>(tag));

    if (EVP_DecryptFinal_ex(ctx, decrypted.data() + len, &len) <= 0) {
        EVP_CIPHER_CTX_free(ctx);
        throw std::runtime_error("Invalid token: decryption failed");
    }
    EVP_CIPHER_CTX_free(ctx);

    return std::string(reinterpret_cast<char*>(decrypted.data()), cipherLen);
}
