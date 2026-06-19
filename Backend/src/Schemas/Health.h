#include <glaze/glaze.hpp>
#include <string>
namespace Schemas {
struct Health {
    bool isHealthy = true;
    std::string message = "Everything is running smoothly";
};
static_assert(glz::reflectable<Health>);
}  // namespace Schemas