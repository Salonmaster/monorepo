#include <drogon/drogon.h>
#include <spdlog/spdlog.h>
#include <spdlog/stopwatch.h>
#include <trantor/utils/Date.h>

using namespace drogon;
class LogRequestMiddleware : public HttpMiddleware<LogRequestMiddleware> {
public:
    LogRequestMiddleware() {};  // do not omit constructor

    void invoke(const HttpRequestPtr& req, MiddlewareNextCallback&& nextCb, MiddlewareCallback&& mcb) override {
        spdlog::stopwatch sw;
        // Do something before calling the next middleware
        nextCb([req, mcb = std::move(mcb), sw](const HttpResponsePtr& resp) {
            // Do something after the next middleware returns
            mcb(resp);
            spdlog::info("{}: {}, {}, {:.3}ms", LogRequestMiddleware::method_to_string(req->method()), req->path(),
                         int(resp->statusCode()), sw.elapsed().count() * 1000);
        });
    }

private:
    static std::string method_to_string(HttpMethod method) {
        switch (method) {
            case HttpMethod::Get:
                return "GET";
            case HttpMethod::Post:
                return "POST";
            case HttpMethod::Head:
                return "HEAD";
            case HttpMethod::Put:
                return "PUT";
            case HttpMethod::Delete:
                return "DELETE";
            case HttpMethod::Options:
                return "OPTIONS";
            case HttpMethod::Patch:
                return "PATCH";
            case HttpMethod::Invalid:
                return "INVALID";
            default:
                return "UNKNOWN";
        }
    }
};
