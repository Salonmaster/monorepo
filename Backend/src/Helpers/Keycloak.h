#pragma once

#include <openssl/sha.h>

#include <drogon/utils/Utilities.h>
#include <string>
#include <regex>

namespace Helpers {

    struct LoginUrlParams {
        std::string baseUrl;
        std::string clientId;
        std::string realm;
        std::string redirectUri;
        std::string codeChallenge;
        std::string state;
    };

    class Keycloak {
    public:
        Keycloak();
        ~Keycloak();

        static bool isValidUuid(const std::string &uuid);
        static std::string generateCodeVerifier();
        static std::string base64url_encode(const std::string &input);
        static std::string generateCodeChallenge(const std::string &verifier);
        static std::string generateLoginUrl(const LoginUrlParams &params);
        static std::string generateTokenUrl(const std::string &baseUrl, const std::string &realm);
    };
} // namespace Helpers
