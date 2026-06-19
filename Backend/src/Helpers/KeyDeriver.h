#pragma once

#include <string>

namespace Helpers {
class KeyDeriver {
public:
    // Derive AES and HMAC keys from a master secret (e.g., 32+ bytes)
    static void deriveKeys(const std::string& masterSecret, std::string& outAesKey, std::string& outHmacKey);
};
}  // namespace Helpers