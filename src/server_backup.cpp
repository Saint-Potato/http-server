// #include <algorithm>
// #include <arpa/inet.h>
// // #include <cstdlib>
// #include <cstring>
// #include <fstream>
// #include <iostream>
// #include <map>
// #include <netdb.h>
// #include <sstream>
// #include <string>
// #include <sys/socket.h>
// #include <sys/types.h>
// #include <thread>
// #include <unistd.h>

// std::string base_dir = "."; // default directory

// // void respond()

// /*
// GET
// /user-agent
// HTTP/1.1
// \r\n

// // Headers
// Host: localhost:4221\r\n
// User-Agent: foobar/1.2.3\r\n  // Read this value
// Accept: /\r\n
// \r\n
// */

// void manage_client_request(int client_fd);

// int main(int argc, char **argv) {
//   // Flush after every std::cout / std::cerr
//   std::cout << std::unitbuf;
//   std::cerr << std::unitbuf;

//   if (argc == 3 && std::string(argv[1]) == "--directory") {
//     base_dir = argv[2];
//   }

//   //   A file descriptor (FD) is a non-negative integer that represents an open
//   //   file, socket, or input/output resource in your program. Think of it as a
//   //   “handle” or “ID” for interacting with system resources.

//   // Host Byte Order - This is the byte order your machine’s CPU uses internally
//   // to store multi-byte values. Little-endian -> Least significant byte first
//   // (used by Intel, AMD CPUs) Big-endian -> Most significant byte first (used
//   // by some network gear, older CPUs) The standard byte order for data
//   // transmitted over the network is big-endian.

//   // creating a new socket, server_fd -> socket file descriptor
//   // SOCK_STREAM: Create a stream socket (i.e., TCP — for HTTP).
//   // 0: Use the default protocol (TCP in this case)
//   int server_fd = socket(AF_INET, SOCK_STREAM, 0);
//   if (server_fd < 0) {
//     std::cerr << "Failed to create server socket\n";
//     return 1; // non-zero status to indicate failure
//   }
//   // socket() returns a number greater or equal than 0 if the connection was
//   // successful or -1 if an error occurred

//   // // Since the tester restarts your program quite often, setting SO_REUSEADDR
//   // // ensures that we don't run into 'Address already in use' errors
//   int reuse = 1;
//   if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse)) <
//       0) {
//     std::cerr << "setsockopt failed\n";
//     return 1;
//   }

//   struct sockaddr_in server_addr; // structure for IPV4 addresses, holds info IP
//                                   // address, port, and protocol family
//   server_addr.sin_family = AF_INET; // AF_INET -> IPV4
//   server_addr.sin_addr.s_addr =
//       INADDR_ANY; // INADDR_ANY = 0.0.0.0 tells the OS to bind to all available
//                   // network interfaces
//   server_addr.sin_port = htons(4221); // sets the port number
//   // htons() = Host TO Network Short Byte Order

//   // bind() associates the socket (server_fd) with IP:Port (0.0.0.0:4221)
//   if (bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) !=
//       0) {
//     std::cerr << "Failed to bind to port 4221\n";
//     return 1;
//   }

//   int connection_backlog = 5; // max number of pending connections that the OS
//                               // can queue up before refusing new ones
//   if (listen(server_fd, connection_backlog) !=
//       0) { // starts listening, it'll now accept incoming connections
//     std::cerr << "listen failed\n";
//     return 1;
//   }

//   while (true) {
//     struct sockaddr_in
//         client_addr; // holds client's address and port after connect
//     int client_addr_len = sizeof(client_addr);

//     std::cout << "Waiting for a client to connect...\n";

//     int client_fd = accept(server_fd, (struct sockaddr *)&client_addr,
//                            (socklen_t *)&client_addr_len);
//     // accept() blocks until a client connects
//     // Takes the listening server_fd.
//     // Fills client_addr with the client’s IP and port.
//     // Returns a new socket file descriptor client_fd for this particular
//     // client.

//     if (client_fd < 0) {
//       std::cout << "Failed to accept connection." << std::endl;
//       continue;
//     }

//     // creating thread for each connection
//     std::thread client_thread(manage_client_request, client_fd);
//     client_thread.detach(); // lets thread run independently
//   }

//   std::cout << "Client connected\n";

//   // close(server_fd);

//   return 0;
// }

// void manage_client_request(int client_fd) {
//   //                <<----------Reading REQUEST----------------------->>
//   char buffer[4096];
//   int bytes_read = recv(client_fd, buffer, sizeof(buffer) - 1, 0);
//   if (bytes_read < 0) {
//     std::cerr << "Failed to read from client.\n";
//     close(client_fd);
//     return;
//   }
//   buffer[bytes_read] = '\0';

//   // Parses the request and extracts method, path and HTTP version
//   std::string request_line = std::strtok(buffer, "\r\n");
//   std::istringstream iss(request_line);
//   std::string method, path, version;
//   iss >> method >> path >> version;

//   // Parse and extract  <--------HEADERS--------------->
//   std::map<std::string, std::string> headers;
//   char *header_line = std::strtok(
//       nullptr, "\r\n"); // continues strtok() after parsing request line
//   while (header_line != nullptr && strlen(header_line) > 0) {
//     std::string line(header_line);
//     int colon_pos = line.find(": ");
//     if (colon_pos != -1) {
//       std::string key = line.substr(0, colon_pos);
//       std::string value = line.substr(colon_pos + 2);
//       // headers names are case insensitive so converting all to lower case
//       std::transform(key.begin(), key.end(), key.begin(), ::tolower);
//       headers[key] = value;
//     }
//     header_line = std::strtok(nullptr, "\r\n");
//   }
//   std::string echo_req = "/echo/";
//   if (method == "GET" && path == "/") {
//     const char *response = "HTTP/1.1 200 OK\r\n\r\n";
//     send(client_fd, response, strlen(response), 0);
//   } else if (method == "GET" && path.rfind(echo_req, 0) == 0) {
//     std::string echo_str = path.substr(echo_req.length()); // Extract {str}
//     std::string body = echo_str;
//     std::string response = "HTTP/1.1 200 OK\r\n"
//                            "Content-Type: text/plain\r\n"
//                            "Content-Length: " +
//                            std::to_string(echo_str.size()) +
//                            "\r\n"
//                            "\r\n" +
//                            echo_str;

//     send(client_fd, response.c_str(), response.size(), 0);

//   } else if (method == "GET" && path == "/user-agent") {
//     std::string user_agent =
//         headers.count("user-agent") ? headers["user-agent"] : "Unknown";

//     std::string response = "HTTP/1.1 200 OK\r\n"
//                            "Content-Type: text/plain\r\n"
//                            "Content-Length: " +
//                            std::to_string(user_agent.size()) +
//                            "\r\n"
//                            "\r\n" +
//                            user_agent;

//     send(client_fd, response.c_str(), response.size(), 0);
//   } else if (method == "GET" && path.rfind("/files/", 0) == 0) {
//     std::string filename = base_dir + "/" + path.substr(std::string("/files/").length());
//     std::ifstream file(filename, std::ios::binary);
//     if (!file.is_open()) {
//       const char *not_found_response = "HTTP/1.1 404 Not Found\r\n\r\n";
//       send(client_fd, not_found_response, strlen(not_found_response), 0);
//     } else {
//       std::ostringstream oss;
//       oss << file.rdbuf();
//       std::string file_content = oss.str();
//       std::string response = "HTTP/1.1 200 OK\r\n"
//                              "Content-Type: application/octet-stream\r\n"
//                              "Content-Length: " +
//                              std::to_string(file_content.size()) + "\r\n\r\n" +
//                              file_content;

//       send(client_fd, response.c_str(), response.size(), 0);
//     }
//   }
//   else if (method == "POST" && path.rfind("/files/", 0) == 0) {
//   std::string filename = path.substr(std::string("/files/").length());
//   std::string full_path = base_dir + "/" + filename;
//   // Content-Length
//   int content_length = 0;
//   if (headers.find("content-length") != headers.end()) {
//     content_length = std::stoi(headers["content-length"]);
//   }

  
//   char* body_start = strstr(buffer, "\r\n\r\n");
//   std::string body;
//   if (body_start != nullptr) {
//     body_start += 4; // skip past \r\n\r\n
//     int header_bytes = body_start - buffer;
//     int body_bytes_already_read = bytes_read - header_bytes;

//   // Start building the body
//     body = std::string(body_start, body_bytes_already_read);

//   // Read the remaining body, if not complete
//   while ((int)body.size() < content_length) {
//     char more[4096];
//     int more_read = recv(client_fd, more, sizeof(more), 0);
//     if (more_read <= 0) break;
//     body.append(more, more_read);
//   }

//   // Write the file
//   std::ofstream out_file(full_path, std::ios::binary);
// if (!out_file.is_open()) {
//   const char* fail = "HTTP/1.1 500 Internal Server Error\r\n\r\n";
//   send(client_fd, fail, strlen(fail), 0);
// } else {
//   out_file.write(body.c_str(), body.size());
//   out_file.close();
//   const char* created = "HTTP/1.1 201 Created\r\n\r\n";
//   send(client_fd, created, strlen(created), 0);
// }
// } else {
//     const char *response = "HTTP/1.1 404 Not Found\r\n\r\n";
//     send(client_fd, response, strlen(response), 0);
//   }
//   close(client_fd);
// }
