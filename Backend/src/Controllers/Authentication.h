
#include <drogon/HttpController.h>
#include <drogon/drogon.h>

#include "Application/Globals.h"
#include "Helpers/Keycloak.h"
#include "Middleware/ExceptionMiddleware.h"
#include "Middleware/LogRequestMiddleware.h"
#include "Middleware/SessionMiddleware.h"
#include "Models/CodeVerifiers.h"
#include "Models/Sessions.h"
namespace Controllers {

class Authentication : public drogon::HttpController<Authentication> {
public:
    METHOD_LIST_BEGIN
    // use METHOD_ADD to add your custom processing function here;
    METHOD_ADD(Authentication::sessionState, "/session", Get, "LogRequestMiddleware", "SessionMiddleware");
    METHOD_ADD(Authentication::authenticate, "/auth", Get, "LogRequestMiddleware");
    METHOD_ADD(Authentication::handleCallback, "/callback", Get, "ExceptionMiddleware", "LogRequestMiddleware");
    METHOD_LIST_END
    // your declaration of processing function maybe like this:
    void sessionState(const drogon::HttpRequestPtr& req,
                      std::function<void(const drogon::HttpResponsePtr&)>&& callback) const;
    void authenticate(const HttpRequestPtr& req, std::function<void(const HttpResponsePtr&)>&& callback) const;
    void handleCallback(const HttpRequestPtr& req, std::function<void(const HttpResponsePtr&)>&& callback) const;
};
}  // namespace Controllers