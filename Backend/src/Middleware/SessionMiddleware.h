#include <Helpers/KeyDeriver.h>
#include <Helpers/SessionCrypto.h>
#include <drogon/drogon.h>
class SessionMiddleware : public drogon::HttpMiddleware<SessionMiddleware> {
public:
    SessionMiddleware() {};  // do not omit constructor

    void invoke(const drogon::HttpRequestPtr& req, drogon::MiddlewareNextCallback&& nextCb,
                drogon::MiddlewareCallback&& mcb) override {
        auto session_cookie = req->getCookie("session");
        if (session_cookie.empty()) {
            mcb(drogon::HttpResponse::newHttpResponse(drogon::k401Unauthorized, drogon::CT_TEXT_PLAIN));
            return;
        }

        // Verify the session cookie
        try {
            std::string aesKey, hmacKey, masterSecret = Application::Globals::instance().masterSecret.unlock();
            Helpers::KeyDeriver::deriveKeys(masterSecret, aesKey, hmacKey);
            Helpers::SessionCrypto sessionCrypto(aesKey, hmacKey);
            // Clear sensitive keys after use
            memset(aesKey.data(), 0, aesKey.size());
            memset(hmacKey.data(), 0, hmacKey.size());
            memset(masterSecret.data(), 0, masterSecret.size());
            // Decrypt and verify the session cookie
            auto decryptedSession = sessionCrypto.decryptAndVerify(session_cookie);
            spdlog::info("Decrypted session: {}", decryptedSession);

            // Fetch session from the database
            auto dbClient = drogon::app().getDbClient();
            auto sessionMapper = drogon::orm::Mapper<drogon_model::backend::Sessions>(dbClient);
            sessionMapper.findByPrimaryKey(
                decryptedSession,
                [mcb, req, nextCb](const drogon_model::backend::Sessions& session) mutable {
                    // If session is found, attach it to the request
                    req->attributes()->insert("session", std::make_shared<drogon_model::backend::Sessions>(session));
                    nextCb([req, mcb = std::move(mcb)](const drogon::HttpResponsePtr& resp) {
                        // Do something after the next middleware returns
                        mcb(resp);
                    });
                },
                [mcb](const drogon::orm::DrogonDbException& e) mutable {
                    spdlog::warn("Session not found or DB error: {}", e.base().what());
                    mcb(drogon::HttpResponse::newHttpResponse(drogon::k401Unauthorized, drogon::CT_TEXT_PLAIN));
                    return;
                });

        } catch (const std::exception& e) {
            spdlog::warn("Failed to decrypt session cookie: {}", e.what());
            mcb(drogon::HttpResponse::newHttpResponse(drogon::k401Unauthorized, drogon::CT_TEXT_PLAIN));
            return;
        }
        // If session cookie is present, continue with the next middleware
    }
};
