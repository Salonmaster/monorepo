#pragma once
#include "../AiAssistant.h"
#include <drogon/HttpController.h>
#include <string>
#include <chrono>

namespace Ai::Handlers {

class ChatRest : public drogon::HttpController<ChatRest> {
public:
    METHOD_LIST_BEGIN
    ADD_METHOD_TO(ChatRest::chat, "/api/v1/chat", drogon::Post);
    ADD_METHOD_TO(ChatRest::conversations, "/api/v1/chat/conversations", drogon::Get);
    ADD_METHOD_TO(ChatRest::deleteConversation, "/api/v1/chat/conversations/{conv_id}", drogon::Delete);
    METHOD_LIST_END

    // POST /api/v1/chat — main chat endpoint (Website chatbot)
    void chat(const drogon::HttpRequestPtr& req,
              std::function<void(const drogon::HttpResponsePtr&)>&& callback) {
        auto json = req->jsonObject();
        if (!json) {
            auto resp = drogon::HttpResponse::newHttpJsonResponse(
                errorJson("Request body must be JSON"));
            resp->setStatusCode(drogon::k400BadRequest);
            callback(resp);
            return;
        }

        auto message = (*json)["message"].asString();
        if (message.empty()) {
            auto resp = drogon::HttpResponse::newHttpJsonResponse(
                errorJson("message is required"));
            resp->setStatusCode(drogon::k400BadRequest);
            callback(resp);
            return;
        }

        auto convId = (*json).get("conversation_id", "").asString();
        auto salonId = (*json).get("salon_id", "default").asString();

        if (convId.empty()) {
            convId = "web-" + salonId + "-" +
                     std::to_string(std::chrono::system_clock::now().time_since_epoch().count());
        }

        auto result = AiAssistant::processMessage(convId, message, salonId);
        auto resp = drogon::HttpResponse::newHttpJsonResponse(result);
        resp->addHeader("Access-Control-Allow-Origin", "*");
        callback(resp);
    }

    // GET /api/v1/chat/conversations — list active conversations
    void conversations(const drogon::HttpRequestPtr& req,
                       std::function<void(const drogon::HttpResponsePtr&)>&& callback) {
        Json::Value result;
        result["conversations"] = Json::Value(Json::arrayValue);
        result["note"] = "Conversation listing not yet implemented";
        auto resp = drogon::HttpResponse::newHttpJsonResponse(result);
        callback(resp);
    }

    // DELETE /api/v1/chat/conversations/{conv_id}
    void deleteConversation(const drogon::HttpRequestPtr& req,
                            std::function<void(const drogon::HttpResponsePtr&)>&& callback,
                            const std::string& convId) {
        ConversationManager::instance().remove(convId);
        Json::Value result;
        result["deleted"] = true;
        auto resp = drogon::HttpResponse::newHttpJsonResponse(result);
        callback(resp);
    }

private:
    static Json::Value errorJson(const std::string& msg) {
        Json::Value e;
        e["error"] = msg;
        return e;
    }
};

} // namespace Ai::Handlers
