#pragma once

#include <memory>
#include <string>

#include "AbstractEncryptor.h"

namespace Helpers {
class DevEncryptor : public AbstractEncryptor {
public:
    explicit DevEncryptor(const std::string& secret);

    std::vector<uint8_t> encrypt(const std::vector<uint8_t>& plaintext) const override;
    std::vector<uint8_t> decrypt(const std::vector<uint8_t>& ciphertext) const override;

    // Destructor
    ~DevEncryptor() override = default;

private:
    std::string m_secret;
};
}  // namespace Helpers