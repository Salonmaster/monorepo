#pragma once
#include "../AiAssistant.h"
#include <drogon/WebSocketController.h>
#include <string>

namespace Ai::Handlers {

class ChatWebSocket : public drogon::WebSocketController<ChatWebSocket> {
public:
    void handleNewMessage(const drogon::WebSocketConnectionPtr& conn,
                          std::string&& message,
                          const drogon::WebSocketMessageType& type) override {
        if (type != drogon::WebSocketMessageType::Text) return;

        Json::Value json;
        Json::CharReaderBuilder builder;
        std::string errs;
        if (!Json::parseFromStream(builder, message.data(),
                                    message.data() + message.size(), &json, &errs)) {
            conn->send("{\"error\":\"Invalid JSON\"}");
            return;
        }

        auto msg = json["message"].asString();
        if (msg.empty()) {
            conn->send("{\"error\":\"message is required\"}");
            return;
        }

        auto salonId = json.get("salon_id", "default").asString();
        auto userId = json.get("user_id", "anonymous").asString();
        auto convId = json.get("conversation_id", salonId + "-" + userId).asString();

        // Process through AI assistant
        auto result = AiAssistant::processMessage(convId, msg, salonId, userId);

        // Send reply back
        Json::Value response;
        response["reply"] = result["reply"];
        response["conversation_id"] = result.get("conversation_id", convId).asString();
        response["timestamp"] = static_cast<Json::Int64>(
            std::chrono::duration_cast<std::chrono::milliseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count());

        conn->send(response.toStyledString());
    }

    void handleNewConnection(const drogon::HttpRequestPtr& req,
                             const drogon::WebSocketConnectionPtr& conn) override {
        spdlog::info("AI Chat WebSocket connected from {}", req->getPeerAddr().toIp());
        conn->send(R"({"reply":"👋 Hi! I'm SalonMaster AI. How can I help you today?","type":"greeting"})");
    }

    void handleConnectionClosed(const drogon::WebSocketConnectionPtr& conn) override {
        spdlog::info("AI Chat WebSocket disconnected");
    }

    WS_PATH_LIST_BEGIN
    WS_PATH_ADD("/chat/ws", drogon::Get);
    WS_PATH_LIST_END
};

} // namespace Ai::Handlers
