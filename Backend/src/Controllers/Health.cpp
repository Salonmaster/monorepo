#include "Health.h"

#include "Schemas/Health.h"
void Controllers::Health::getHealthStatus(const HttpRequestPtr& req,
                                          std::function<void(const HttpResponsePtr&)>&& callback) const {
    Schemas::Health healthStatus;
    auto resp = HttpResponse::newHttpResponse();
    auto f = drogon::app().getDbClient()->execSqlAsyncFuture("select 1");
    try {
        auto result = f.get();  // Block until we get the result or catch the exception;
        healthStatus.isHealthy = result.size() == 1;
    } catch (const std::exception& e) {
        spdlog::error("Database error: {}", e.what());
        healthStatus.isHealthy = false;
        healthStatus.message = "Database connection failed or query error";
    }

    resp->setBody(*glz::write_json(healthStatus));
    resp->setStatusCode(healthStatus.isHealthy ? k200OK : k500InternalServerError);
    resp->setContentTypeCode(CT_APPLICATION_JSON);
    callback(resp);
}
