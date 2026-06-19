
/**
 * @file AbstractEncryptor.h
 * @brief Defines the abstract interface for encryption and decryption helpers.
 *
 * @copyright
 * Copyright (c) 2024. All rights reserved.
 *
 * @details
 * This file declares the Helpers::AbstractEncryptor class, which provides a generic
 * interface for encryption and decryption operations on both binary and string data.
 */

/// @brief Standard library includes for byte vectors, strings, and fixed-width integers.
#include <cstdint>
#include <string>
#include <vector>

namespace Helpers {

/**
 * @class AbstractEncryptor
 * @brief Abstract base class for encryption and decryption functionality.
 *
 * Provides a generic interface for encrypting and decrypting data, supporting both
 * binary (std::vector<uint8_t>) and string (std::string) formats. Derived classes
 * must implement the binary encrypt and decrypt methods.
 */
class AbstractEncryptor {
public:
    /**
     * @brief Virtual destructor.
     */
    virtual ~AbstractEncryptor() = default;

    /**
     * @brief Encrypts binary data.
     * @param plaintext The data to encrypt as a vector of bytes.
     * @return The encrypted data as a vector of bytes.
     */
    virtual std::vector<uint8_t> encrypt(const std::vector<uint8_t>& plaintext) const = 0;

    /**
     * @brief Decrypts binary data.
     * @param ciphertext The data to decrypt as a vector of bytes.
     * @return The decrypted data as a vector of bytes.
     */
    virtual std::vector<uint8_t> decrypt(const std::vector<uint8_t>& ciphertext) const = 0;

    /**
     * @brief Encrypts a string.
     * @param plaintext The string to encrypt.
     * @return The encrypted string.
     *
     * @note Converts the input string to a byte vector, encrypts it, and returns the result as a string.
     */
    std::string encrypt(const std::string& plaintext) const;

    /**
     * @brief Decrypts a string.
     * @param ciphertext The string to decrypt.
     * @return The decrypted string.
     *
     * @note Converts the input string to a byte vector, decrypts it, and returns the result as a string.
     */
    std::string decrypt(const std::string& ciphertext) const;
};

}  // namespace Helpers