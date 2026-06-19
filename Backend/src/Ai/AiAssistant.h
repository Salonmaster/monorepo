#pragma once
#include "ConversationManager.h"
#include "DeepSeekProvider.h"
#include "ToolRegistry.h"
#include "Tools/BookAppointment.h"
#include "Tools/ClientTools.h"
#include "Tools/QueryRevenue.h"
#include "Tools/SalonInfo.h"
#include "../../Application/Globals.h"
#include <drogon/drogon.h>
#include <memory>
#include <string>

namespace Ai {

class AiAssistant {
public:
    static AiAssistant& instance() {
        static AiAssistant assistant;
        return assistant;
    }

    void initialize() {
        auto& cfg = Application::Globals::instance();
        // Read API key from environment or drogon config
        std::string apiKey;
        auto* envKey = std::getenv("DEEPSEEK_API_KEY");
        if (envKey) {
            apiKey = envKey;
        } else {
            // Try drogon config custom_config.ai.deepseek_api_key
            auto& jsonCfg = drogon::app().getCustomConfig();
            if (jsonCfg.isMember("ai") && jsonCfg["ai"].isMember("deepseek_api_key")) {
                apiKey = jsonCfg["ai"]["deepseek_api_key"].asString();
            }
        }

        provider_ = std::make_unique<DeepSeekProvider>(apiKey);
        model_ = "deepseek-chat";
        systemPrompt_ =
            "You are SalonMaster AI, the helpful assistant for SalonMaster — a Point of Sale "
            "system for hair, nail, and beauty salons. You help salon owners, staff, and "
            "clients with booking appointments, checking revenue, managing clients, and "
            "answering questions about salon services. "
            "Be friendly, concise, and salon-savvy. Use emojis occasionally. 💈\n\n"
            "When asked to DO something (book, check, look up), use the available tools. "
            "When asked a general question, answer helpfully from your knowledge.\n\n"
            "Important: today's date is " + currentDate() + ". "
            "Use this as the default date unless the user specifies otherwise.";

        // Register all tools
        Tools::registerRevenueTools();
        Tools::registerBookingTools();
        Tools::registerClientTools();
        Tools::registerSalonInfoTools();

        // Periodic cleanup
        cleanupTimerId_ = drogon::app().getLoop()->runEvery(3600.0, []() {
            ConversationManager::instance().cleanup();
        });

        spdlog::info("🤖 AI Assistant initialized ({} tools, model: {})",
                     ToolRegistry::instance().tools().size(), model_);
    }

    void shutdown() {
        if (cleanupTimerId_ != drogon::InvalidTimerId) {
            drogon::app().getLoop()->invalidateTimer(cleanupTimerId_);
        }
    }

    static Json::Value processMessage(const std::string& conversationId,
                                       const std::string& message,
                                       const std::string& salonId = "",
                                       const std::string& userId = "") {
        return instance().processMessageImpl(conversationId, message, salonId, userId);
    }

private:
    std::unique_ptr<DeepSeekProvider> provider_;
    std::string model_;
    std::string systemPrompt_;
    drogon::TimerId cleanupTimerId_;

    static std::string currentDate() {
        auto now = std::chrono::system_clock::now();
        auto t = std::chrono::system_clock::to_time_t(now);
        std::ostringstream oss;
        oss << std::put_time(std::localtime(&t), "%Y-%m-%d");
        return oss.str();
    }

    Json::Value processMessageImpl(const std::string& conversationId,
                                    const std::string& message,
                                    const std::string& salonId,
                                    const std::string& userId) {
        auto conv = ConversationManager::instance().getOrCreate(
            conversationId, salonId, userId);

        if (conv->messages().empty()) {
            conv->setSystemPrompt(systemPrompt_);
        }

        ChatMessage userMsg;
        userMsg.role = "user";
        userMsg.content = message;
        conv->addMessage(userMsg);

        auto tools = ToolRegistry::instance().toFunctionDefinitions();
        return runConversationLoop(conv, tools);
    }

    Json::Value runConversationLoop(std::shared_ptr<Conversation> conv,
                                     const Json::Value& tools) {
        const int maxIterations = 5;

        for (int i = 0; i < maxIterations; i++) {
            auto messages = conv->toApiMessages();
            AiResponse resp;

            try {
                resp = provider_->chat(messages, tools);
            } catch (const std::exception& e) {
                spdlog::error("AI provider error: {}", e.what());
                Json::Value err;
                err["reply"] = "Sorry, I'm having trouble right now. Try again in a moment.";
                return err;
            }

            if (resp.hasToolCall) {
                ChatMessage assistantMsg;
                assistantMsg.role = "assistant";
                assistantMsg.content = "";
                assistantMsg.toolCallId = resp.toolCallId;
                assistantMsg.toolName = resp.toolName;
                conv->addMessage(assistantMsg);

                auto toolResult = ToolRegistry::instance().callTool(
                    resp.toolName, resp.toolArgs);

                spdlog::info("AI tool call: {} → {}", resp.toolName,
                             resp.toolArgs.toStyledString().substr(0, 100));

                ChatMessage toolMsg;
                toolMsg.role = "tool";
                toolMsg.toolCallId = resp.toolCallId;
                toolMsg.toolName = resp.toolName;
                toolMsg.content = toolResult.toStyledString();
                conv->addMessage(toolMsg);

                continue;
            }

            ChatMessage assistantMsg;
            assistantMsg.role = "assistant";
            assistantMsg.content = resp.content;
            conv->addMessage(assistantMsg);

            Json::Value result;
            result["reply"] = resp.content;
            result["conversation_id"] = conv->id();
            return result;
        }

        Json::Value err;
        err["reply"] = "Let me simplify — what would you like help with?";
        return err;
    }
};

} // namespace Ai
