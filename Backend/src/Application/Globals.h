#pragma once

/**
 * @file globals.h
 * @brief Singleton class to store all global variables for the application.
 */

#include <Types/SecureMasterKey.h>

#include <boost/filesystem.hpp>
#include <mutex>
#include <string>

namespace Application {
/**
 * @class Globals
 * @brief Singleton to store and manage global variables.
 */
class Globals {
public:
    /**
     * @brief Get the singleton instance of Globals.
     * @return Reference to the Globals instance.
     */
    static Globals& instance() {
        static Globals instance;
        return instance;
    }

    const std::string appName = APP_NAME;        ///< Name of the application
    const std::string appVersion = APP_VERSION;  ///< Version of the application (from CMake)
    Types::SecureMasterKey masterSecret =
        Types::SecureMasterKey("");  ///< Master secret for key derivation (should be set securely)

    // Keycloak configuration
    bool keycloakEnable = false;                              ///< Enable Keycloak authentication
    std::string keycloakClientId = "backend";                 ///< Keycloak client ID
    std::string keycloakClientSecret = "secret";              ///< Keycloak client secret
    std::string keycloakRealm = "master";                     ///< Keycloak realm
    std::string keycloakServerUrl = "http://127.0.0.1:8080";  ///< Keycloak server URL
    std::string keycloakRedirectUri =
        "http://localhost/Controllers/Authentication/callback";              ///< Keycloak redirect URI
    std::string keycloakLogoutRedirectUri = "http://127.0.0.1/auth/logout";  ///< Keycloak logout redirect URI
    // Example global variables
    std::string configFilePath = "config.json";  ///< Path to the configuration file

    // Delete copy/move constructors and assignment operators
    Globals(const Globals&) = delete;
    Globals& operator=(const Globals&) = delete;
    Globals(Globals&&) = delete;
    Globals& operator=(Globals&&) = delete;

private:
    /**
     * @brief Private constructor for singleton pattern.
     */
    Globals() = default;

    /**
     * @brief Destructor.
     */
    ~Globals() = default;
};
}  // namespace Application