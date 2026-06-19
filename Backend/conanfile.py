from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
from conan.tools.cmake import CMakeToolchain, CMakeDeps

class BackendRecipe(ConanFile):
    name = "backend"
    version = "0.1"
    settings = "os", "compiler", "build_type", "arch"
    generators = "CMakeToolchain", "CMakeDeps"
    requires = [
        "drogon/1.9.13",
        "spdlog/1.15.2",
        "cli11/2.5.0",
        "glaze/5.4.0",
        "jsoncpp/1.9.6"
    ]
    def configure(self):
        self.options["drogon"].with_ctl = True
        self.options["drogon"].with_postgres = True   
        self.options["drogon"].with_yaml_cpp = True
        self.options["drogon"].with_postgres_batch = True


    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()