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


/**
 * Manages the server's lifecycle, including socket setup and connection acceptance.
 *
 * This class encapsulates the core server functionality. It initializes the listening socket,
 * binds it to a specific port, and enters a loop to accept and handle incoming client connections.
 */
class HttpServer {
private:
    int server_fd;  // File descriptor for the listening server socket.
    std::string base_dir;   // The root directory for serving files.
    int port;   // The port number the server will listen on.


    void setupSocket();     // Creates, configures (with SO_REUSEADDR), binds, and sets the socket to listen for incoming connections.
    

    /**
     * Enters an infinite loop to accept new client connections.
     *
     * For each new connection, it spawns a new thread to handle the client's requests.
     */
    void acceptConnections();
public:
    HttpServer(const std::string& directory, int port = 4221);

    /**
     * Starts the server's execution.
     *
     * Calls setupSocket() and then acceptConnections() to begin listening for clients.
     */
    void start();
};


/**
 * @class HttpRequest
 * @brief Represents a parsed HTTP request.
 *
 * This class provides a structured representation of an incoming HTTP request,
 * breaking it down into its method, path, version, headers, and body.
 */
class HttpRequest {
    
public:
    std::string method;
    std::string path;
    std::string version;
    std::map<std::string, std::string> headers;
    std::string body;

    static HttpRequest parse(int client_fd, char* buffer, int bytes_read);
};

/**
 * @class HttpResponse
 * @brief Handles the creation and sending of HTTP responses.
 *
 * This class simplifies sending responses back to the client, handling the formatting
 * of status lines, headers, and the response body.
 */
class HttpResponse {
private:
    int client_fd;      // File descriptor for the client socket to write the response to.
    bool should_close;     // Flag to determine if the 'Connection: close' header should be sent.

public:
    HttpResponse(int client_fd, bool should_close = false);

    /**
     * @brief Sends a fully formatted HTTP response with a body.
     * @param status The HTTP status string (e.g., "200 OK").
     * @param content_type The MIME type of the body (e.g., "text/plain").
     * @param body The content to send in the response body.
     */
    void sendResponse(const std::string& status, const std::string& content_type,
                      const std::string& body);

    /**
     * @brief Sends a raw string as a response.
     *
     * Useful for sending responses without a body or with custom headers.
     * @param raw The raw HTTP response string to send.
     */
    void sendRaw(const std::string& raw);
};


/**
 * @class RequestHandler
 * @brief Contains the application logic for routing and handling requests.
 *
 * This class inspects the HttpRequest and determines the appropriate action,
 * such as returning an echo, serving a file, or creating a new file.
 */
class RequestHandler {
private:
    std::string base_dir;  // The working directory for file operations.
public:
    RequestHandler(const std::string& dir);

    /**
     * @brief Handles an incoming request and uses the HttpResponse object to send a reply.
     * @param request The parsed HttpRequest object.
     * @param response The HttpResponse object used to send the response.
     */
    void handle(const HttpRequest& request, HttpResponse& response);
};


/**
 * @brief The function executed by each client thread.
 *
 * This function manages the lifecycle of a single client connection. It reads requests,
 * processes them, sends responses, and handles persistent connections (keep-alive).
 * @param client_fd The file descriptor for the connected client's socket.
 * @param base_dir The root directory for file operations.
 */
void handleClient(int client_fd, const std::string& base_dir);