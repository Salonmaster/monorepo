#pragma once
#include "Tool.h"
#include <drogon/drogon.h>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <vector>

namespace Ai {

class ToolRegistry {
public:
    static ToolRegistry& instance() {
        static ToolRegistry registry;
        return registry;
    }

    void registerTool(Tool tool) {
        std::lock_guard<std::mutex> lock(mutex_);
        tools_[tool.name] = std::move(tool);
        spdlog::info("AI Tool registered: {}", tool.name);
    }

    const std::unordered_map<std::string, Tool>& tools() const {
        return tools_;
    }

    Tool* get(const std::string& name) {
        auto it = tools_.find(name);
        return it != tools_.end() ? &it->second : nullptr;
    }

    // Serialize all tool definitions for LLM function-calling API
    Json::Value toFunctionDefinitions() const {
        Json::Value functions(Json::arrayValue);
        for (const auto& [name, tool] : tools_) {
            Json::Value func;
            func["name"] = name;
            func["description"] = tool.description;

            Json::Value params;
            params["type"] = "object";
            Json::Value properties(Json::objectValue);
            Json::Value required(Json::arrayValue);

            for (const auto& param : tool.parameters) {
                Json::Value prop;
                prop["type"] = param.type;
                prop["description"] = param.description;
                properties[param.name] = prop;
                if (param.required) {
                    required.append(param.name);
                }
            }

            params["properties"] = properties;
            if (!required.empty()) {
                params["required"] = required;
            }
            func["parameters"] = params;
            functions.append(func);
        }
        return functions;
    }

    Json::Value callTool(const std::string& name, const Json::Value& args) {
        auto* tool = get(name);
        if (!tool) {
            Json::Value err;
            err["error"] = "Unknown tool: " + name;
            return err;
        }
        try {
            return tool->handler(args);
        } catch (const std::exception& e) {
            Json::Value err;
            err["error"] = std::string("Tool error: ") + e.what();
            return err;
        }
    }

private:
    ToolRegistry() = default;
    std::mutex mutex_;
    std::unordered_map<std::string, Tool> tools_;
};

} // namespace Ai
