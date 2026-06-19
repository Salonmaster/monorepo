#pragma once
#include <drogon/drogon.h>
#include <chrono>
#include <string>
#include <vector>

namespace Ai {

struct ChatMessage {
    std::string role;  // "system", "user", "assistant", "tool"
    std::string content;
    std::string toolCallId;
    std::string toolName;
    std::chrono::steady_clock::time_point timestamp;
};

class Conversation {
public:
    explicit Conversation(const std::string& id, const std::string& salonId = "",
                          const std::string& userId = "")
        : id_(id), salonId_(salonId), userId_(userId),
          createdAt_(std::chrono::steady_clock::now()) {
    }

    void addMessage(ChatMessage msg) {
        msg.timestamp = std::chrono::steady_clock::now();
        messages_.push_back(std::move(msg));
        // Keep last 50 messages for context window
        if (messages_.size() > 50) {
            // Always keep system message
            auto keepFrom = messages_.size() - 49;
            if (!messages_.empty() && messages_[0].role == "system") {
                keepFrom = 1;
            }
            messages_.erase(messages_.begin() + keepFrom, messages_.end() - 49);
        }
    }

    void setSystemPrompt(const std::string& prompt) {
        if (!messages_.empty() && messages_[0].role == "system") {
            messages_[0].content = prompt;
        } else {
            ChatMessage sys;
            sys.role = "system";
            sys.content = prompt;
            sys.timestamp = std::chrono::steady_clock::now();
            messages_.insert(messages_.begin(), sys);
        }
    }

    const std::vector<ChatMessage>& messages() const { return messages_; }
    const std::string& id() const { return id_; }
    const std::string& salonId() const { return salonId_; }
    const std::string& userId() const { return userId_; }

    std::chrono::steady_clock::time_point lastActivity() const {
        return messages_.empty() ? createdAt_ : messages_.back().timestamp;
    }

    // Convert to LLM API format
    Json::Value toApiMessages() const {
        Json::Value arr(Json::arrayValue);
        for (const auto& msg : messages_) {
            Json::Value m;
            m["role"] = msg.role;
            m["content"] = msg.content;
            if (!msg.toolCallId.empty()) {
                m["tool_call_id"] = msg.toolCallId;
            }
            if (!msg.toolName.empty()) {
                m["name"] = msg.toolName;
            }
            arr.append(m);
        }
        return arr;
    }

private:
    std::string id_;
    std::string salonId_;
    std::string userId_;
    std::vector<ChatMessage> messages_;
    std::chrono::steady_clock::time_point createdAt_;
};

} // namespace Ai
