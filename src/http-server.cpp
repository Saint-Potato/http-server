#include "http-server.hpp"
std::string base_dir = "."; // default directory

// void respond()

/*
GET
/user-agent
HTTP/1.1
\r\n

// Headers
Host: localhost:4221\r\n
User-Agent: foobar/1.2.3\r\n  // Read this value
Accept: /\r\n
\r\n
*/

  //   A file descriptor (FD) is a non-negative integer that represents an open
  //   file, socket, or input/output resource in your program. Think of it as a
  //   “handle” or “ID” for interacting with system resources.

  // Host Byte Order - This is the byte order your machine’s CPU uses internally
  // to store multi-byte values. Little-endian -> Least significant byte first
  // (used by Intel, AMD CPUs) Big-endian -> Most significant byte first (used
  // by some network gear, older CPUs) The standard byte order for data
  // transmitted over the network is big-endian.

HttpServer::HttpServer(const std::string& directory, int port)
    : base_dir(directory), port(port), server_fd(-1) {}

void HttpServer::start() {
    setupSocket();
    acceptConnections();
}

void HttpServer::setupSocket() {
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd < 0) {
        std::cerr << "Failed to create server socket\n";
        exit(1); // non-zero status to indicate failure
    }

    // Since the tester restarts your program quite often, setting SO_REUSEADDR ensures that we don't run into 'Address already in use' errors
    int reuse = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) < 0) {
        std::cerr << "setsockopt failed\n";
        exit(1);
    }

    sockaddr_in server_addr{};  // structure for IPV4 addresses, holds info IP address, port, and protocol family
    server_addr.sin_family = AF_INET;  
    // AF_INET -> IPV4
    server_addr.sin_addr.s_addr = INADDR_ANY;  
    // INADDR_ANY = 0.0.0.0 tells the OS to bind to all available network interfaces
    server_addr.sin_port = htons(port);  
    // sets the port number
    // htons() = Host To Network Short Byte Order

    if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) != 0) {
        std::cerr << "Failed to bind to port " << port << "\n";
        exit(1);
    }

    int backlog = 5;
    // max number of pending connections that the OS can queue up before refusing new ones
    if (listen(server_fd, backlog) != 0) {
        std::cerr << "listen failed\n";
        exit(1);
    }

    std::cout << "[HttpServer] Listening on port " << port << std::endl;
}

void HttpServer::acceptConnections() {
    while (true) {
        sockaddr_in client_addr{};
        // holds client's address and port after connect

        socklen_t client_len = sizeof(client_addr);
        std::cout << "Waiting for a client to connect...\n";

        int client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &client_len);
        // accept() blocks until a client connects
        // Takes the listening server_fd.
        // Fills client_addr with the client’s IP and port.
        // Returns a new socket file descriptor client_fd for this particular
        // client.
        if (client_fd < 0) {
            std::cerr << "Failed to accept connection.\n";
            continue;
        }

        std::thread client_thread(manage_client_request, client_fd);
        client_thread.detach();
    }
}

HttpRequest HttpRequest::parse(int client_fd, char* buffer, int bytes_read) {
    HttpRequest request;
    buffer[bytes_read] = '\0'; // Null-terminate to safely work with strtok

    // Parsing Request Line
    std::string request_line = std::strtok(buffer, "\r\n");
    std::istringstream iss(request_line);
    iss >> request.method >> request.path >> request.version;

    // Parsing Headers
    std::map<std::string, std::string> headers;
    char* header_line = std::strtok(nullptr, "\r\n");
    // continues strtok() after parsing request line
    while (header_line != nullptr && strlen(header_line) > 0) {
        std::string line(header_line);
        int colon_pos = line.find(": ");
        if (colon_pos != -1) {
            std::string key = line.substr(0, colon_pos);
            std::string value = line.substr(colon_pos + 2);
            std::transform(key.begin(), key.end(), key.begin(), ::tolower);
            // headers names are case insensitive so converting all to lower case
            headers[key] = value;
        }
        header_line = std::strtok(nullptr, "\r\n");
    }
    request.headers = headers;

    // Parse Body if Content-Length present
    int content_length = 0;
    if (headers.find("content-length") != headers.end()) {
        content_length = std::stoi(headers["content-length"]);
    }

    char* body_start = strstr(buffer, "\r\n\r\n");
    if (body_start != nullptr) {
        body_start += 4; // skip past \r\n\r\n
        int header_bytes = body_start - buffer;
        int body_bytes_already_read = bytes_read - header_bytes;

        request.body = std::string(body_start, body_bytes_already_read);

        // If full body not yet read, read remaining
        while ((int)request.body.size() < content_length) {
            char more[4096];
            int more_read = recv(client_fd, more, sizeof(more), 0);
            if (more_read <= 0) break;
            request.body.append(more, more_read);
        }
    }

    return request;
}


HttpResponse::HttpResponse(int client_fd) : client_fd(client_fd) {}

void HttpResponse::sendResponse(const std::string& status, const std::string& content_type,
                                const std::string& body) {
    std::ostringstream oss;
    oss << "HTTP/1.1 " << status << "\r\n"
        << "Content-Type: " << content_type << "\r\n"
        << "Content-Length: " << body.size() << "\r\n"
        << "\r\n"
        << body;

    std::string response = oss.str();
    send(client_fd, response.c_str(), response.size(), 0);
}

void HttpResponse::sendRaw(const std::string& raw) {
    send(client_fd, raw.c_str(), raw.size(), 0);
}


RequestHandler::RequestHandler(const std::string& dir) : base_dir(dir) {}

void RequestHandler::handle(const HttpRequest& request, HttpResponse& response) {
    const std::string& method = request.method;
    const std::string& path = request.path;

    if (method == "GET" && path == "/") {
        response.sendRaw("HTTP/1.1 200 OK\r\n\r\n");
    }
    else if (method == "GET" && path.rfind("/echo/", 0) == 0) {
        std::string echo_str = path.substr(std::string("/echo/").length());
        response.sendResponse("200 OK", "text/plain", echo_str);
    }
    else if (method == "GET" && path == "/user-agent") {
        auto it = request.headers.find("user-agent");
        std::string user_agent = (it != request.headers.end()) ? it->second : "Unknown";
        response.sendResponse("200 OK", "text/plain", user_agent);
    }
    else if (method == "GET" && path.rfind("/files/", 0) == 0) {
        std::string filename = base_dir + "/" + path.substr(std::string("/files/").length());
        std::ifstream file(filename, std::ios::binary);
        if (!file.is_open()) {
            response.sendRaw("HTTP/1.1 404 Not Found\r\n\r\n");
        } else {
            std::ostringstream oss;
            oss << file.rdbuf();
            std::string content = oss.str();
            response.sendResponse("200 OK", "application/octet-stream", content);
        }
    }
    else if (method == "POST" && path.rfind("/files/", 0) == 0) {
        std::string filename = path.substr(std::string("/files/").length());
        std::string full_path = base_dir + "/" + filename;

        std::ofstream out_file(full_path, std::ios::binary);
        if (!out_file.is_open()) {
            response.sendRaw("HTTP/1.1 500 Internal Server Error\r\n\r\n");
        } else {
            out_file.write(request.body.c_str(), request.body.size());
            out_file.close();
            response.sendRaw("HTTP/1.1 201 Created\r\n\r\n");
        }
    }
    else {
        response.sendRaw("HTTP/1.1 404 Not Found\r\n\r\n");
    }
}




  
