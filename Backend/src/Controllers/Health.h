#include <drogon/HttpController.h>
#include <drogon/drogon.h>

#include "Middleware/LogRequestMiddleware.h"

namespace Controllers {

class Health : public drogon::HttpController<Health> {
public:
    METHOD_LIST_BEGIN
    // use METHOD_ADD to add your custom processing function here;
    METHOD_ADD(Health::getHealthStatus, "/status", Get, "LogRequestMiddleware");
    METHOD_LIST_END
    // your declaration of processing function maybe like this:
    void getHealthStatus(const HttpRequestPtr& req, std::function<void(const HttpResponsePtr&)>&& callback) const;
};
}  // namespace Controllers