#pragma once

#include <string>
namespace Helpers {
    class SessionCrypto {
    public:
        SessionCrypto(const std::string &aesKey, const std::string &hmacKey);
        ~SessionCrypto();

        std::string encryptAndSign(const std::string &sessionId);
        std::string decryptAndVerify(const std::string &tokenBase64);

    private:
        std::string aesKey_;
        std::string hmacKey_;

        static constexpr size_t IV_LENGTH = 12;
        static constexpr size_t TAG_LENGTH = 16;
        static constexpr size_t HMAC_LENGTH = 32;
    };
}
