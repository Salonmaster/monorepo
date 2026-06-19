#pragma once
#include "Conversation.h"
#include <drogon/drogon.h>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>

namespace Ai {

class ConversationManager {
public:
    static ConversationManager& instance() {
        static ConversationManager mgr;
        return mgr;
    }

    std::shared_ptr<Conversation> getOrCreate(const std::string& id,
                                               const std::string& salonId = "",
                                               const std::string& userId = "") {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = conversations_.find(id);
        if (it != conversations_.end()) {
            return it->second;
        }
        auto conv = std::make_shared<Conversation>(id, salonId, userId);
        conversations_[id] = conv;
        return conv;
    }

    void remove(const std::string& id) {
        std::lock_guard<std::mutex> lock(mutex_);
        conversations_.erase(id);
    }

    // Clean up conversations older than 24h
    void cleanup() {
        std::lock_guard<std::mutex> lock(mutex_);
        auto now = std::chrono::steady_clock::now();
        auto it = conversations_.begin();
        while (it != conversations_.end()) {
            auto age = std::chrono::duration_cast<std::chrono::hours>(
                now - it->second->lastActivity()).count();
            if (age > 24) {
                it = conversations_.erase(it);
            } else {
                ++it;
            }
        }
    }

private:
    ConversationManager() = default;
    std::mutex mutex_;
    std::unordered_map<std::string, std::shared_ptr<Conversation>> conversations_;
};

} // namespace Ai
