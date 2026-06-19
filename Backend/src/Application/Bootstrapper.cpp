#include "Bootstrapper.h"

bool Application::Bootstrapper::processCommandLineArguments(int argc, char** argv) {
    CLI::App app{Globals::instance().appName + " " + Globals::instance().appVersion};
    argv = app.ensure_utf8(argv);

    app.add_option("-c,--config", Globals::instance().configFilePath, "Path to the config file")
        ->default_val(Globals::instance().configFilePath)
        ->check(CLI::ExistingFile)
        ->description("Path to the configuration file");

    CLI11_PARSE(app, argc, argv);
    return true;  // Placeholder for actual implementation
}

bool Application::Bootstrapper::loadConfiguration() {
    spdlog::info("Loading configuration from: {}", Globals::instance().configFilePath);
    try {
        drogon::app().loadConfigFile(Globals::instance().configFilePath);
    } catch (const std::exception& e) {
        spdlog::warn(e.what());
    }
    // Load configuration logic here
    Json::Value root;
    Json::CharReaderBuilder builder;
    std::ifstream configFile(Globals::instance().configFilePath, std::ifstream::binary);
    if (!configFile) {
        spdlog::error("Failed to open config file: {}", Globals::instance().configFilePath);
        return false;
    }
    std::string errs;
    if (!Json::parseFromStream(builder, configFile, &root, &errs)) {
        spdlog::error("Failed to parse config file: {}", errs);
        return false;
    }

    // Parse "keycloak" and "app" sections efficiently
    auto& globals = Application::Globals::instance();
    if (const auto& keycloak = root["keycloak"]; !keycloak.isNull()) {
        globals.keycloakClientId = keycloak.get("client_id", globals.keycloakClientId).asString();
        globals.keycloakClientSecret = keycloak.get("client_secret", globals.keycloakClientSecret).asString();
        globals.keycloakRealm = keycloak.get("realm", globals.keycloakRealm).asString();
        globals.keycloakServerUrl = keycloak.get("server_url", globals.keycloakServerUrl).asString();
    } else {
        spdlog::warn("No 'keycloak' section found in config.");
    }
    if (const auto& appConfig = root["app"]; !appConfig.isNull()) {
        globals.masterSecret = Types::SecureMasterKey(appConfig.get("master_key", "").asString());
    } else {
        spdlog::warn("No 'app' section found in config.");
    }

    return true;  // Placeholder for actual implementation
}

bool Application::Bootstrapper::configureLogging() {
    spdlog::info("Configuring logging...");
    return true;  // Placeholder for actual implementation
}

bool Application::Bootstrapper::printBanner() {
    spdlog::info("Welcome to {} version {}", Globals::instance().appName, Globals::instance().appVersion);
    return true;  // Placeholder for actual implementation
}

bool Application::Bootstrapper::startServer() {
    spdlog::info("Starting server...");
    for (const auto& listener : drogon::app().getListeners()) {
        spdlog::info("Listening on {}:{}", listener.toIp(), listener.toPort());
    }
    drogon::app().run();
    // Server startup logic here
    // Return true if successful, false otherwise
    return true;  // Placeholder for actual implementation
}

bool Application::Bootstrapper::run(int argc, char** argv) {
    std::vector<std::function<bool()>> initializers = {
        [argc, argv]() { return processCommandLineArguments(argc, argv); }, []() { return configureLogging(); },
        []() { return loadConfiguration(); }, []() { return printBanner(); }, []() { return startServer(); }};
    for (const auto& init : initializers) {
        if (!init()) {
            return false;
        }
    }

    // If everything goes well, return true
    return true;
}