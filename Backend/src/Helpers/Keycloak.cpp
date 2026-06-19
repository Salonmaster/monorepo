#include "Keycloak.h"

bool Helpers::Keycloak::isValidUuid(const std::string& uuid) {
    static const std::regex uuidRegex(
        R"(^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$)",
        std::regex::ECMAScript);
    return std::regex_match(uuid, uuidRegex);
}

std::string Helpers::Keycloak::generateCodeVerifier() {
    std::string chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~";
    std::string verifier;
    for (int i = 0; i < 64; ++i) {
        verifier += chars[rand() % chars.size()];
    }
    return verifier;
}

std::string Helpers::Keycloak::base64url_encode(const std::string& input) {
    std::string encoded = drogon::utils::base64Encode(input);
    // Convert to URL-safe base64
    std::string result;
    for (char c : encoded) {
        if (c == '+')
            result += '-';
        else if (c == '/')
            result += '_';
        else if (c == '=')
            continue;
        else
            result += c;
    }
    return result;
}

std::string Helpers::Keycloak::generateCodeChallenge(const std::string& verifier) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256(reinterpret_cast<const unsigned char*>(verifier.c_str()), verifier.length(), hash);
    return base64url_encode(std::string(reinterpret_cast<char*>(hash), SHA256_DIGEST_LENGTH));
}

std::string Helpers::Keycloak::generateLoginUrl(const LoginUrlParams& params) {
    return params.baseUrl + "/realms/" + params.realm +
           "/protocol/openid-connect/auth"
           "?client_id=" +
           params.clientId + "&redirect_uri=" + drogon::utils::urlEncode(params.redirectUri) + "&response_type=code" +
           "&code_challenge=" + params.codeChallenge + "&code_challenge_method=S256" + "&state=" + params.state;
}
std::string Helpers::Keycloak::generateTokenUrl(const std::string& baseUrl, const std::string& realm) {
    return baseUrl + "/realms/" + realm + "/protocol/openid-connect/token";
}