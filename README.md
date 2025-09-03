# HTTP Server in C++

This is a simple HTTP server implemented in C++.

## Features

*   Handles multiple concurrent connections.
*   Persistent connections (Keep-Alive).
*   Responds to basic requests with appropriate status codes (200 OK, 404 Not Found, 201 Created).
*   Parses request paths, headers, and bodies.
*   Serves files from a specified directory.
*   Handles POST requests to create files.
*   Echoes back request bodies and user agents.

## Requirements

*   C++23 compatible compiler
*   pthreads

## Running the Server

To run the server, use the provided script:

```sh
./your_program.sh
```

The server will start and listen on port 4221 by default.

## Testing

To run the tests, execute the script from the project's root directory:

```sh
python3 complete_test.py
```

The server has been tested for various functionalities, including:
*   Binding to a port
*   Responding with 200 OK
*   Extracting URL paths
*   Responding with a body
*   Reading request headers
*   Handling concurrent connections
*   Returning and creating files
*   Persistent connections

All tests passed successfully.
