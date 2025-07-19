#include <algorithm>
#include <arpa/inet.h>
// #include <cstdlib>
#include <cstring>
#include <fstream>
#include <iostream>
#include <map>
#include <netdb.h>
#include <sstream>
#include <string>
#include <sys/socket.h>
#include <sys/types.h>
#include <thread>
#include <unistd.h>

class HttpServer {
private:
    int server_fd;
    std::string base_dir;
    int port;
    void setupSocket();
    void acceptConnections();
public:
    HttpServer(const std::string& directory, int port = 4221);
    void start();
};

class HttpRequest {
    // Parse the raw HTTP request into structured components (method, path, headers, body)
public:
    std::string method;
    std::string path;
    std::string version;
    std::map<std::string, std::string> headers;
    std::string body;

    static HttpRequest parse(int client_fd, char* buffer, int bytes_read);
};

class HttpResponse {
private:
    int client_fd;
    bool should_close;
public:
    HttpResponse(int client_fd, bool should_close = false);
    void sendResponse(const std::string& status, const std::string& content_type,
                      const std::string& body);
    void sendRaw(const std::string& raw);
};


// Contains the logic for responding to GET /, /echo/*, /user-agent, file GET/POST.
class RequestHandler {
private:
    std::string base_dir;  // working directory
public:
    RequestHandler(const std::string& dir);
    void handle(const HttpRequest& request, HttpResponse& response);
};

void handleClient(int client_fd, const std::string& base_dir);