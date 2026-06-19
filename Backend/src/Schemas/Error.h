#include <glaze/glaze.hpp>

#include <string>
namespace Schemas{
  struct Error
  {
    std::string message = "An unexpected error occurred";
  };

  static_assert(glz::reflectable<Error>);
}