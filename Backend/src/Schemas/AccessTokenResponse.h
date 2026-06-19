#pragma once
#include <glaze/glaze.hpp>
#include <string>
namespace Schemas {

struct AccessTokenResponse {
    std::string access_token;
    int expires_in;
    int refresh_expires_in;
    std::string refresh_token;
    std::string token_type;
    int not_before_policy;
    std::string session_state;
    std::string scope;
};
static_assert(glz::reflectable<AccessTokenResponse>);

}  // namespace Schemas