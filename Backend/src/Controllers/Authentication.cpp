#include "Authentication.h"

#include "Helpers/KeyDeriver.h"
#include "Helpers/SessionCrypto.h"
#include "Schemas/AccessTokenResponse.h"
#include "Schemas/Error.h"

void Controllers::Authentication::sessionState(const drogon::HttpRequestPtr& req,
                                               std::function<void(const HttpResponsePtr&)>&& callback) const {
    auto session = req->attributes()->get<std::shared_ptr<drogon_model::backend::Sessions>>("session");
    auto resp = HttpResponse::newHttpResponse();
    resp->setStatusCode(k200OK);
    resp->setContentTypeCode(drogon::CT_APPLICATION_JSON);
    resp->setBody(*glz::write_json(Schemas::Error{*session->getAccessToken()}));
    callback(resp);
}

void Controllers::Authentication::authenticate(const HttpRequestPtr& req,
                                               std::function<void(const HttpResponsePtr&)>&& callback) const {
    // Generate a code verifier and code challenge for PKCE
    auto codeVerifier = drogon_model::backend::CodeVerifiers();
    codeVerifier.setId(drogon::utils::getUuid());  // Set a unique ID for the code verifier
    codeVerifier.setVerifier(Helpers::Keycloak::generateCodeVerifier());
    codeVerifier.setCodeChallenge(Helpers::Keycloak::generateCodeChallenge(*codeVerifier.getVerifier()));
    codeVerifier.setCodeChallengeMethod("S256");

    Helpers::LoginUrlParams params{Application::Globals::instance().keycloakServerUrl,
                                   Application::Globals::instance().keycloakClientId,
                                   Application::Globals::instance().keycloakRealm,
                                   Application::Globals::instance().keycloakRedirectUri,
                                   *codeVerifier.getCodeChallenge(),
                                   *codeVerifier.getId()};

    // Store the verifier in the session or a secure place for later use
    auto dbClient = drogon::app().getDbClient();
    auto codeVerifierMapper = drogon::orm::Mapper<drogon_model::backend::CodeVerifiers>(dbClient);
    codeVerifierMapper.insertFuture(codeVerifier).wait();

    auto loginUrl = Helpers::Keycloak::generateLoginUrl(params);
    callback(HttpResponse::newRedirectionResponse(loginUrl, k307TemporaryRedirect));
}

void Controllers::Authentication::handleCallback(const HttpRequestPtr& req,
                                                 std::function<void(const HttpResponsePtr&)>&& callback) const {
    auto code = req->getParameter("code"), state = req->getParameter("state");
    if (code.empty() || state.empty() && !Helpers::Keycloak::isValidUuid(state)) {
        callback(HttpResponse::newNotFoundResponse());
        return;
    }

    // Fetch the code verifier using the state parameter
    auto dbClient = drogon::app().getDbClient();
    auto codeVerifierMapper = drogon::orm::Mapper<drogon_model::backend::CodeVerifiers>(dbClient);

    codeVerifierMapper.findByPrimaryKey(
        state,
        [code, callback, dbClient, req](const drogon_model::backend::CodeVerifiers& verifier) mutable {
            // Now we fetch the tokens from keycloak using the code and verifier
            auto tokenBaseUrl = Application::Globals::instance().keycloakServerUrl;
            auto tokenPath = Helpers::Keycloak::generateTokenUrl("", Application::Globals::instance().keycloakRealm);

            auto keycloakReq = HttpRequest::newHttpFormPostRequest();
            keycloakReq->setMethod(HttpMethod::Post);
            keycloakReq->setPath(tokenPath);
            keycloakReq->setParameter("grant_type", "authorization_code");
            keycloakReq->setParameter("code", code);
            keycloakReq->setParameter("redirect_uri", Application::Globals::instance().keycloakRedirectUri);
            keycloakReq->setParameter("client_id", Application::Globals::instance().keycloakClientId);
            keycloakReq->setParameter("code_verifier", *verifier.getVerifier());
            keycloakReq->setParameter("client_secret", Application::Globals::instance().keycloakClientSecret);

            auto client = HttpClient::newHttpClient(Application::Globals::instance().keycloakServerUrl, app().getLoop(),
                                                    false, false);
            client->sendRequest(
                keycloakReq, [req, callback, dbClient, verifier](ReqResult result, const HttpResponsePtr& response) {
                    if (result == ReqResult::Ok && response) {
                        // Decode the response
                        glz::context ctx{};
                        Schemas::AccessTokenResponse tokenResponse;
                        glz::read<glz::opts{.error_on_unknown_keys = false}>(tokenResponse, response->getBody(), ctx);

                        // Create session or store the token as needed
                        auto sessionMapper = drogon::orm::Mapper<drogon_model::backend::Sessions>(dbClient);

                        drogon_model::backend::Sessions session;
                        session.setAccessToken(tokenResponse.access_token);
                        session.setRefreshToken(tokenResponse.refresh_token);
                        session.setExpiresIn(tokenResponse.expires_in);
                        session.setRefreshExpiresIn(tokenResponse.refresh_expires_in);
                        session.setTokenType(tokenResponse.token_type);
                        session.setNotBeforePolicy(tokenResponse.not_before_policy);
                        session.setSessionState(tokenResponse.session_state);
                        session.setScope(tokenResponse.scope);
                        session.setId(drogon::utils::getUuid());  // Set a unique ID for the session
                        session.setVerifier(*verifier.getVerifier());
                        session.setCodeChallenge(*verifier.getCodeChallenge());
                        session.setCodeChallengeMethod(*verifier.getCodeChallengeMethod());

                        sessionMapper.insert(session);

                        auto resp = HttpResponse::newHttpResponse();
                        resp->setBody(*glz::write_json(tokenResponse));
                        resp->setStatusCode(k200OK);

                        // Generate and set a secure cookie
                        std::string aesKey, hmacKey;
                        Helpers::KeyDeriver::deriveKeys(Application::Globals::instance().masterSecret.unlock(), aesKey,
                                                        hmacKey);
                        Helpers::SessionCrypto sessionCrypto(aesKey, hmacKey);
                        drogon::Cookie cookie("session", sessionCrypto.encryptAndSign(*session.getId()));
                        cookie.setHttpOnly(true);
                        cookie.setSecure(true);
                        cookie.setSameSite(drogon::Cookie::SameSite::kStrict);
                        cookie.setPath("/");
                        cookie.setMaxAge(3600);  // Set cookie to expire in 1 hour
                        resp->addCookie(std::move(cookie));

                        // Handle successful token response
                        callback(resp);
                    } else {
                        // Handle error response
                        callback(HttpResponse::newNotFoundResponse());
                    }
                });

            drogon::orm::Mapper<drogon_model::backend::CodeVerifiers> nonConstMapper(dbClient);
            nonConstMapper.deleteFutureOne(verifier);

            // auto response = HttpResponse::newHttpResponse();
            // response->setStatusCode(k200OK);
            // response->setContentTypeCode(drogon::CT_TEXT_PLAIN);
            // response->setBody("Authentication successful. Code: " + *verifier.getVerifier() +
            //                   ", Code Challenge: " + *verifier.getCodeChallenge());

            // callback(response);
        },
        [callback](const drogon::orm::DrogonDbException& e) {
            auto response = HttpResponse::newHttpResponse();
            response->setStatusCode(k500InternalServerError);
            response->setContentTypeCode(drogon::CT_APPLICATION_JSON);
            response->setBody(*glz::write_json(Schemas::Error{"Failed to find code verifier."}));
            callback(response);
        });
}
