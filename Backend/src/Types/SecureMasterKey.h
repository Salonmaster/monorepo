// SecureMasterKey.h
#pragma once

#include <string>
#include <vector>
namespace Types
{
    class SecureMasterKey {
    public:
        explicit SecureMasterKey(const std::string& rawKey);
        ~SecureMasterKey();

        std::string unlock();

    private:
        std::vector<unsigned char> encrypted_; // AES-CTR encrypted key in memory
        std::vector<unsigned char> iv_;        // Random IV used for encryption
        std::vector<unsigned char> tempKey_;   // Zeroed after use

        void clearSensitive(std::vector<unsigned char>& vec);
        void encryptInMemory(const std::string& plain);
        std::string decryptInMemory();
    };
}