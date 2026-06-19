#include <drogon/drogon.h>

#include <iostream>

#include "Ai/AiAssistant.h"
#include "Application/Bootstrapper.h"

int main(int argc, char** argv) {
    if (!Application::Bootstrapper::run(argc, argv)) {
        std::cerr << "Application failed to start." << std::endl;
        return 1;
    }

    // Initialize AI Assistant
    Ai::AiAssistant::instance().initialize();

    return 0;
}
