#pragma once
#include "ToolRegistry.h"
#include <drogon/drogon.h>
#include <string>

namespace Ai {

struct AiResponse {
    std::string content;
    bool hasToolCall = false;
    std::string toolName;
    Json::Value toolArgs;
    std::string toolCallId;
};

class DeepSeekProvider {
public:
    DeepSeekProvider(const std::string& apiKey, const std::string& baseUrl = "")
        : apiKey_(apiKey), baseUrl_(baseUrl.empty() ? "https://api.deepseek.com" : baseUrl) {
    }

    // Stream-friendly chat completion with tool support
    AiResponse chat(const Json::Value& messages, const Json::Value& tools) {
        auto resp = sendRequest(messages, tools);
        return parseResponse(resp);
    }

    AiResponse chatSimple(const Json::Value& messages) {
        Json::Value empty;
        auto resp = sendRequest(messages, empty);
        return parseResponse(resp);
    }

private:
    std::string apiKey_;
    std::string baseUrl_;

    Json::Value sendRequest(const Json::Value& messages, const Json::Value& tools) {
        auto client = drogon::HttpClient::newHttpClient(baseUrl_);
        auto req = drogon::HttpRequest::newHttpRequest();
        req->setPath("/v1/chat/completions");
        req->setMethod(drogon::Post);
        req->setContentTypeCode(drogon::CT_APPLICATION_JSON);
        req->addHeader("Authorization", "Bearer " + apiKey_);

        Json::Value body;
        body["model"] = "deepseek-chat";
        body["messages"] = messages;
        body["max_tokens"] = 2048;
        body["temperature"] = 0.7;

        if (!tools.empty() && tools.isArray() && !tools.empty()) {
            body["tools"] = tools;
            body["tool_choice"] = "auto";
        }

        req->setBody(body.toStyledString());

        auto [result, response] = client->sendRequest(req, 30.0);
        if (result != drogon::ReqResult::Ok || !response) {
            throw std::runtime_error("AI provider request failed");
        }

        Json::Value json;
        Json::CharReaderBuilder builder;
        std::string errs;
        auto bodyStr = std::string(response->body());
        if (!Json::parseFromStream(builder, bodyStr.data(),
                                    bodyStr.data() + bodyStr.size(), &json, &errs)) {
            throw std::runtime_error("Failed to parse AI response: " + errs);
        }
        return json;
    }

    AiResponse parseResponse(const Json::Value& json) {
        AiResponse resp;
        auto& choices = json["choices"];
        if (choices.empty()) {
            resp.content = "Sorry, I couldn't process that.";
            return resp;
        }

        auto& msg = choices[0]["message"];

        // Check for tool calls
        if (msg.isMember("tool_calls") && !msg["tool_calls"].empty()) {
            auto& toolCall = msg["tool_calls"][0];
            resp.hasToolCall = true;
            resp.toolCallId = toolCall["id"].asString();
            resp.toolName = toolCall["function"]["name"].asString();

            auto argsStr = toolCall["function"]["arguments"].asString();
            Json::CharReaderBuilder builder;
            std::string errs;
            Json::parseFromStream(builder, argsStr.data(),
                                  argsStr.data() + argsStr.size(),
                                  &resp.toolArgs, &errs);
        }

        if (msg.isMember("content") && !msg["content"].isNull()) {
            resp.content = msg["content"].asString();
        }

        return resp;
    }
};

} // namespace Ai
