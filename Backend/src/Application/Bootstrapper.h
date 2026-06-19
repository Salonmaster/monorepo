#pragma once

//STD Framework includes
#include <vector>
#include <functional>

//Third party includes
#include <json/json.h>
#include <spdlog/spdlog.h>
#include <drogon/drogon.h>
#include <CLI/CLI.hpp>

//Local includes
#include "Globals.h"

/**
 * @file bootstrapper.h
 * @brief Declares the Bootstrapper class for application startup and shutdown.
 */

namespace Application
{
    /**
     * @class Bootstrapper
     * @brief Handles application initialization and main run loop.
     */
    class Bootstrapper
    {
    private:
        /* data */
    public:
     /**
         * @brief Runs the application.
         * @param argc The number of command line arguments.
         * @param argv The command line arguments.
         * @return true if the application ran successfully, false otherwise.
         */
        static bool run(int argc, char** argv);

    private:
        // Private members can be added here if needed in the future
        static bool processCommandLineArguments(int argc, char** argv);
        static bool loadConfiguration();
        static bool configureLogging();
        static bool printBanner();
        static bool startServer();
    };
}
