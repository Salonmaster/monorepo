#include <drogon/drogon.h>

#include <iostream>

#include "Application/Bootstrapper.h"

int main(int argc, char** argv) {
    if (!Application::Bootstrapper::run(argc, argv)) {
        std::cerr << "Application failed to start." << std::endl;
        return 1;
    }
    return 0;
}