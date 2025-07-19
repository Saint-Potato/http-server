#include "http-server.hpp"

int main(int argc, char **argv){

    // Flush after every std::cout / std::cerr
    std::cout << std::unitbuf;
    std::cerr << std::unitbuf;

    std::string base_dir = ".";
    if (argc == 3 && std::string(argv[1]) == "--directory") {
    base_dir = argv[2];
    }

    HttpServer server(base_dir);
    server.start();


    return 0;
}