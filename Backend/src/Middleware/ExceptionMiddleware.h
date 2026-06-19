#include <drogon/drogon.h>

#include <trantor/utils/Date.h>

using namespace drogon;
class ExceptionMiddleware : public HttpMiddleware<ExceptionMiddleware>
{
public:
    ExceptionMiddleware(){};  // do not omit constructor

    void invoke(const HttpRequestPtr &req,
                MiddlewareNextCallback &&nextCb,
                MiddlewareCallback &&mcb) override
    {
        try
        {
            nextCb([req, mcb = std::move(mcb)](const HttpResponsePtr &resp) {
                // Do something after the next middleware returns
                mcb(resp);
            });
        }
        catch(const std::exception& e)
        {
            auto resp = HttpResponse::newHttpResponse();
            resp->setStatusCode(k500InternalServerError);
            resp->setContentTypeCode(CT_TEXT_PLAIN);
            resp->setBody("Internal Server Error: " + std::string(e.what()));
            mcb(resp);
        }
        
        // Do something before calling the next middleware


    }


};
