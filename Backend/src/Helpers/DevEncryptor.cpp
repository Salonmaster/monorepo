#include "DevEncryptor.h"

std::vector<uint8_t> Helpers::DevEncryptor::encrypt(const std::vector<uint8_t>& plaintext) const {
    // For development, we simply return the plaintext as is
    return plaintext;
}

std::vector<uint8_t> Helpers::DevEncryptor::decrypt(const std::vector<uint8_t>& ciphertext) const {
    // For development, we simply return the ciphertext as is
    return ciphertext;
}