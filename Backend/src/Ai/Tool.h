#pragma once
#include <drogon/drogon.h>
#include <functional>
#include <string>
#include <vector>

namespace Ai {

struct ToolParameter {
    std::string name;
    std::string type;        // "string", "number", "boolean", "array", "object"
    std::string description;
    bool required = false;
};

struct ToolDefinition {
    std::string name;
    std::string description;
    std::vector<ToolParameter> parameters;
    std::function<Json::Value(const Json::Value&)> handler;
};

using Tool = ToolDefinition;

} // namespace Ai
