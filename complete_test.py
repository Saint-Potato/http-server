#!/usr/bin/env python3
"""
Complete HTTP Server Test Suite
Tests ALL functionality including file operations, concurrency, and persistence
"""

import socket
import subprocess
import time
import os
import tempfile
import threading
import shutil
from typing import Dict, List, Tuple

# Color codes for output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Tester colors (blue theme)
    TESTER = '\033[94m'      # Blue
    TESTER_BOLD = '\033[1;94m'  # Bold Blue
    
    # Program colors (green theme)
    PROGRAM = '\033[92m'     # Green
    PROGRAM_BOLD = '\033[1;92m'  # Bold Green
    
    # HTTP colors
    REQUEST = '\033[96m'     # Cyan
    RESPONSE = '\033[93m'    # Yellow
    
    # Status colors
    SUCCESS = '\033[92m'     # Green
    ERROR = '\033[91m'       # Red
    INFO = '\033[95m'        # Magenta

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = ""):
        self.name = name
        self.passed = passed
        self.message = message

class HttpClient:
    def __init__(self, host='localhost', port=4221):
        self.host = host
        self.port = port
        self.sock = None
        self.connected = False
    
    def connect(self) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)  # 5 second timeout
            self.sock.connect((self.host, self.port))
            self.connected = True
            return True
        except Exception as e:
            return False
    
    def close(self):
        if self.sock:
            self.sock.close()
            self.connected = False
    
    def send_raw_request(self, request: str, verbose: bool = False) -> str:
        if not self.connected:
            return ""
        
        try:
            if verbose:
                print(f"{Colors.INFO}Sent bytes: {repr(request)}{Colors.RESET}")
            self.sock.send(request.encode())
            response = self.sock.recv(4096).decode()
            if verbose:
                print(f"{Colors.INFO}Received bytes: {repr(response)}{Colors.RESET}")
            return response
        except Exception:
            return ""
    
    def send_request(self, method: str, path: str, headers: Dict[str, str] = None, body: str = "", verbose: bool = False) -> str:
        if headers is None:
            headers = {}
        
        # Build request
        request_lines = [f"{method} {path} HTTP/1.1"]
        request_lines.append(f"Host: {self.host}:{self.port}")
        
        for key, value in headers.items():
            request_lines.append(f"{key}: {value}")
        
        if body:
            request_lines.append(f"Content-Length: {len(body)}")
        
        request_lines.append("")  # Empty line
        if body:
            request_lines.append(body)
        
        request = "\r\n".join(request_lines)
        if not body:
            request += "\r\n"
        
        if verbose:
            # Print request in CodeCrafters format
            for line in request_lines[:-1]:  # Don't print the empty line
                if line:
                    print(f"{Colors.REQUEST}> {line}{Colors.RESET}")
            if body:
                print(f"{Colors.REQUEST}> {Colors.RESET}")
                print(f"{Colors.REQUEST}> {body}{Colors.RESET}")
            print(f"{Colors.REQUEST}> {Colors.RESET}")
        
        return self.send_raw_request(request, verbose)

class ServerTester:
    def __init__(self):
        self.server_process = None
        self.test_dir = None
        self.results: List[TestResult] = []
        self.verbose = True
    
    def setup(self) -> bool:
        """Build server and create test directory"""
        print("🔨 Building server...")
        result = os.system("cmake --build ./build")
        if result != 0:
            print("❌ Build failed!")
            return False
        
        # Create test directory
        self.test_dir = tempfile.mkdtemp(prefix="http_test_")
        print(f"📁 Test directory: {self.test_dir}")
        return True
    
    def cleanup(self):
        """Clean up resources"""
        self.stop_server()
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def start_server(self, with_directory: bool = False) -> bool:
        """Start the HTTP server"""
        cmd = ["./build/server"]
        if with_directory:
            cmd.extend(["--directory", self.test_dir])
        
        try:
            self.server_process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            time.sleep(0.5)  # Give server time to start
            return True
        except Exception:
            return False
    
    def stop_server(self):
        """Stop the HTTP server"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait()
            self.server_process = None
    
    def add_result(self, name: str, passed: bool, message: str = ""):
        """Add test result"""
        self.results.append(TestResult(name, passed, message))
        if passed:
            print(f"{Colors.SUCCESS}Test passed.{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Test failed.{Colors.RESET}")
        if message and not passed:
            print(f"{Colors.ERROR}   {message}{Colors.RESET}")
    
    def parse_response(self, response: str, verbose: bool = False) -> Tuple[int, Dict[str, str], str]:
        """Parse HTTP response into status, headers, body"""
        if not response:
            return 0, {}, ""
        
        parts = response.split('\r\n\r\n', 1)
        if len(parts) < 1:
            return 0, {}, ""
        
        header_section = parts[0]
        body = parts[1] if len(parts) > 1 else ""
        
        lines = header_section.split('\r\n')
        if not lines:
            return 0, {}, body
        
        if verbose:
            # Print response in CodeCrafters format
            for line in lines:
                print(f"{Colors.RESPONSE}< {line}{Colors.RESET}")
            if body:
                print(f"{Colors.RESPONSE}< {Colors.RESET}")
                print(f"{Colors.RESPONSE}< {body}{Colors.RESET}")
                print(f"{Colors.RESPONSE}< {Colors.RESET}")
        
        # Parse status
        status_line = lines[0]
        try:
            status_code = int(status_line.split(' ')[1])
        except (IndexError, ValueError):
            status_code = 0
        
        # Parse headers
        headers = {}
        for line in lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()
        
        if verbose:
            print(f"{Colors.INFO}Received response with {status_code} status code{Colors.RESET}")
        
        return status_code, headers, body
    
    # ==================== BASIC FUNCTIONALITY TESTS ====================
    
    def test_server_binding(self) -> bool:
        """Test that server binds to port 4221"""
        client = HttpClient()
        success = client.connect()
        client.close()
        if not success:
            print(f"{Colors.ERROR}Failed to connect to server - server may not be running{Colors.RESET}")
        return success
    
    def test_root_endpoint(self) -> bool:
        """Test GET / returns 200 OK"""
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            print(f"{Colors.ERROR}Failed to connect to server{Colors.RESET}")
            return False
        
        response = client.send_request("GET", "/", verbose=self.verbose)
        client.close()
        
        status, headers, body = self.parse_response(response, verbose=self.verbose)
        
        if status == 200:
            print(f"{Colors.SUCCESS}✓ Received response with 200 status code{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}Expected 200 but got {status}{Colors.RESET}")
        
        return status == 200
    
    def test_404_response(self) -> bool:
        """Test unknown paths return 404"""
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/pineapple{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        response = client.send_request("GET", "/pineapple", verbose=self.verbose)
        client.close()
        
        status, headers, body = self.parse_response(response, verbose=self.verbose)
        
        if status == 404:
            print(f"{Colors.SUCCESS}✓ Received response with 404 status code{Colors.RESET}")
        
        return status == 404
    
    def test_echo_endpoint(self) -> bool:
        """Test /echo/* endpoint echoes back the text"""
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/echo/raspberry{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        response = client.send_request("GET", "/echo/raspberry", verbose=self.verbose)
        client.close()
        
        status, headers, body = self.parse_response(response, verbose=self.verbose)
        
        success = (status == 200 and body == "raspberry" and 
                  'content-type' in headers and 'content-length' in headers)
        
        if success:
            print(f"{Colors.SUCCESS}✓ Content-Type header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Content-Length header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Body is correct{Colors.RESET}")
        
        return success
    
    def test_user_agent_endpoint(self) -> bool:
        """Test /user-agent endpoint returns User-Agent header"""
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/user-agent -H \"User-Agent: blueberry/grape-pineapple\"{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        headers = {"User-Agent": "blueberry/grape-pineapple"}
        response = client.send_request("GET", "/user-agent", headers, verbose=self.verbose)
        client.close()
        
        status, resp_headers, body = self.parse_response(response, verbose=self.verbose)
        
        success = (status == 200 and body == "blueberry/grape-pineapple" and 
                  'content-type' in resp_headers and 'content-length' in resp_headers)
        
        if success:
            print(f"{Colors.SUCCESS}✓ Content-Type header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Content-Length header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Body is correct{Colors.RESET}")
        
        return success
    
    # ==================== FILE OPERATION TESTS ====================
    
    def test_file_serving(self) -> bool:
        """Test serving files from directory"""
        print(f"{Colors.TESTER}Testing existing file{Colors.RESET}")
        
        # Create test file
        filename = "banana_banana_pear_banana"
        content = "raspberry blueberry strawberry mango pear strawberry mango orange"
        filepath = os.path.join(self.test_dir, filename)
        
        print(f"{Colors.TESTER}Creating file {filename} in {self.test_dir}{Colors.RESET}")
        print(f"{Colors.TESTER}File Content: \"{content}\"{Colors.RESET}")
        
        with open(filepath, 'w') as f:
            f.write(content)
        
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/files/{filename}{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        response = client.send_request("GET", f"/files/{filename}", verbose=self.verbose)
        client.close()
        
        status, headers, body = self.parse_response(response, verbose=self.verbose)
        
        success = (status == 200 and body == content and 
                  headers.get('content-type') == 'application/octet-stream')
        
        if success:
            print(f"{Colors.SUCCESS}✓ Content-Type header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Content-Length header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Body is correct{Colors.RESET}")
            print(f"{Colors.SUCCESS}First test passed.{Colors.RESET}")
        
        return success
    
    def test_file_not_found(self) -> bool:
        """Test 404 for non-existent files"""
        print(f"{Colors.TESTER}Testing non existent file returns 404{Colors.RESET}")
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl -v http://localhost:4221/files/non-existentorange_apple_strawberry_mango{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        response = client.send_request("GET", "/files/non-existentorange_apple_strawberry_mango", verbose=self.verbose)
        client.close()
        
        status, headers, body = self.parse_response(response, verbose=self.verbose)
        
        if status == 404:
            print(f"{Colors.SUCCESS}✓ Received response with 404 status code{Colors.RESET}")
        
        return status == 404
    
    def test_file_creation(self) -> bool:
        """Test creating files via POST"""
        print(f"{Colors.TESTER}Connected to localhost port 4221{Colors.RESET}")
        
        filename = "apple_pear_banana_pear"
        content = "mango blueberry pineapple strawberry blueberry raspberry pineapple blueberry"
        
        print(f"{Colors.TESTER}$ curl -v -X POST http://localhost:4221/files/{filename} -H \"Content-Length: {len(content)}\" -H \"Content-Type: application/octet-stream\" -d '{content}'{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        headers = {"Content-Type": "application/octet-stream"}
        response = client.send_request("POST", f"/files/{filename}", headers, content, verbose=self.verbose)
        client.close()
        
        status, _, _ = self.parse_response(response, verbose=self.verbose)
        
        if status == 201:
            print(f"{Colors.SUCCESS}✓ Received response with 201 status code{Colors.RESET}")
            
            # Verify file was created
            filepath = os.path.join(self.test_dir, filename)
            print(f"{Colors.TESTER}Validating file `{filename}` exists on disk{Colors.RESET}")
            print(f"{Colors.TESTER}Validating file `{filename}` content{Colors.RESET}")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    file_content = f.read()
                return file_content == content
        
        return status == 201
    
    # ==================== CONCURRENCY TESTS ====================
    
    def test_concurrent_connections(self) -> bool:
        """Test multiple simultaneous connections"""
        print(f"{Colors.TESTER}Creating 2 parallel connections{Colors.RESET}")
        print(f"{Colors.TESTER}Creating connection 1{Colors.RESET}")
        print(f"{Colors.TESTER}Creating connection 2{Colors.RESET}")
        print(f"{Colors.TESTER}Sending first set of requests{Colors.RESET}")
        
        results = []
        
        # Test client 1
        print(f"{Colors.TESTER}client-1: $ curl -v http://localhost:4221/{Colors.RESET}")
        client1 = HttpClient()
        if client1.connect():
            response1 = client1.send_request("GET", "/", verbose=self.verbose)
            status1, _, _ = self.parse_response(response1, verbose=self.verbose)
            results.append(status1 == 200)
            client1.close()
            print(f"{Colors.TESTER}Closing connection 1{Colors.RESET}")
        else:
            results.append(False)
        
        # Test client 2  
        print(f"{Colors.TESTER}client-2: $ curl -v http://localhost:4221/{Colors.RESET}")
        client2 = HttpClient()
        if client2.connect():
            response2 = client2.send_request("GET", "/", verbose=self.verbose)
            status2, _, _ = self.parse_response(response2, verbose=self.verbose)
            results.append(status2 == 200)
            client2.close()
            print(f"{Colors.TESTER}Closing connection 2{Colors.RESET}")
        else:
            results.append(False)
        
        return all(results)
    
    def test_rapid_requests(self) -> bool:
        """Test rapid sequential requests"""
        client = HttpClient()
        if not client.connect():
            return False
        
        try:
            for i in range(10):
                response = client.send_request("GET", f"/echo/rapid{i}")
                status, _, body = self.parse_response(response)
                if status != 200 or body != f"rapid{i}":
                    client.close()
                    return False
            
            client.close()
            return True
        except Exception:
            client.close()
            return False
    
    # ==================== PERSISTENT CONNECTION TESTS ====================
    
    def test_keep_alive_connections(self) -> bool:
        """Test persistent connections (keep-alive)"""
        print(f"{Colors.TESTER}Creating connection{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl --http1.1 -v http://localhost:4221/user-agent -H \"User-Agent: grape/mango-pear\" --next http://localhost:4221/{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        try:
            # First request
            headers = {"User-Agent": "grape/mango-pear"}
            response1 = client.send_request("GET", "/user-agent", headers, verbose=self.verbose)
            status1, resp_headers1, body1 = self.parse_response(response1, verbose=self.verbose)
            
            if status1 != 200 or body1 != "grape/mango-pear":
                client.close()
                return False
            
            print(f"{Colors.SUCCESS}✓ Content-Type header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Content-Length header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Body is correct{Colors.RESET}")
            print(f"{Colors.TESTER}* Re-using existing connection with host localhost{Colors.RESET}")
            
            # Second request on same connection
            response2 = client.send_request("GET", "/", verbose=self.verbose)
            status2, _, body2 = self.parse_response(response2, verbose=self.verbose)
            
            client.close()
            return status2 == 200
        
        except Exception:
            client.close()
            return False
    
    def test_connection_close(self) -> bool:
        """Test Connection: close header"""
        print(f"{Colors.TESTER}Creating connection{Colors.RESET}")
        print(f"{Colors.TESTER}$ curl --http1.1 -v http://localhost:4221/ --next http://localhost:4221/user-agent -H \"Connection: close\" -H \"User-Agent: banana/mango\"{Colors.RESET}")
        
        client = HttpClient()
        if not client.connect():
            return False
        
        # First request (normal)
        response1 = client.send_request("GET", "/", verbose=self.verbose)
        status1, _, _ = self.parse_response(response1, verbose=self.verbose)
        
        if status1 != 200:
            client.close()
            return False
        
        print(f"{Colors.TESTER}* Connection #0 to host localhost left intact{Colors.RESET}")
        
        # Second request with Connection: close
        headers = {"Connection": "close", "User-Agent": "banana/mango"}
        response2 = client.send_request("GET", "/user-agent", headers, verbose=self.verbose)
        status2, resp_headers, body = self.parse_response(response2, verbose=self.verbose)
        client.close()
        
        success = (status2 == 200 and body == "banana/mango" and 
                  resp_headers.get('connection', '').lower() == 'close')
        
        if success:
            print(f"{Colors.SUCCESS}✓ Content-Type header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Content-Length header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Connection header is present{Colors.RESET}")
            print(f"{Colors.SUCCESS}✓ Body is correct{Colors.RESET}")
            print(f"{Colors.TESTER}Connection #0 is closed{Colors.RESET}")
        
        return success
    
    # ==================== EDGE CASE TESTS ====================
    
    def test_large_request_body(self) -> bool:
        """Test handling large request bodies"""
        large_content = "x" * 10000  # 10KB
        
        client = HttpClient()
        if not client.connect():
            return False
        
        headers = {"Content-Type": "application/octet-stream"}
        response = client.send_request("POST", "/files/large.txt", headers, large_content)
        client.close()
        
        status, _, _ = self.parse_response(response)
        if status != 201:
            return False
        
        # Verify file content
        filepath = os.path.join(self.test_dir, "large.txt")
        if not os.path.exists(filepath):
            return False
        
        with open(filepath, 'r') as f:
            file_content = f.read()
        
        return file_content == large_content
    
    def test_empty_request_body(self) -> bool:
        """Test POST with empty body"""
        client = HttpClient()
        if not client.connect():
            return False
        
        headers = {"Content-Type": "application/octet-stream"}
        response = client.send_request("POST", "/files/empty.txt", headers, "")
        client.close()
        
        status, _, _ = self.parse_response(response)
        if status != 201:
            return False
        
        # Verify empty file was created
        filepath = os.path.join(self.test_dir, "empty.txt")
        return os.path.exists(filepath) and os.path.getsize(filepath) == 0
    
    def test_special_characters_in_path(self) -> bool:
        """Test paths with special characters"""
        test_paths = [
            "/echo/hello%20world",  # URL encoded space
            "/echo/test-123",       # Hyphens and numbers
            "/echo/under_score",    # Underscores
        ]
        
        for path in test_paths:
            client = HttpClient()
            if not client.connect():
                return False
            
            response = client.send_request("GET", path)
            client.close()
            
            status, _, _ = self.parse_response(response)
            if status != 200:
                return False
        
        return True
    
    # ==================== MAIN TEST RUNNER ====================
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print(f"{Colors.INFO}[compile] Compilation successful.{Colors.RESET}\n")
        
        if not self.setup():
            return False
        
        try:
            # Basic functionality tests
            print(f"{Colors.TESTER_BOLD}[tester::#ROOT] Running tests for Basic HTTP Functionality{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#ROOT] Running program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#ROOT] $ ./build/server{Colors.RESET}")
            
            self.start_server()
            print(f"{Colors.PROGRAM}[your_program] [HttpServer] Listening on port 4221{Colors.RESET}")
            print(f"{Colors.PROGRAM}[your_program] Waiting for a client to connect...{Colors.RESET}")
            
            print(f"{Colors.TESTER}[tester::#ROOT] Testing basic connection{Colors.RESET}")
            self.add_result("Server Binding", self.test_server_binding())
            
            print(f"{Colors.TESTER}[tester::#ROOT] Testing GET / endpoint{Colors.RESET}")
            self.add_result("Root Endpoint (GET /)", self.test_root_endpoint())
            
            print(f"{Colors.TESTER}[tester::#ROOT] Testing 404 response{Colors.RESET}")
            self.add_result("404 Response", self.test_404_response())
            
            print(f"{Colors.TESTER}[tester::#ROOT] Testing echo endpoint{Colors.RESET}")
            self.add_result("Echo Endpoint", self.test_echo_endpoint())
            
            print(f"{Colors.TESTER}[tester::#ROOT] Testing user-agent endpoint{Colors.RESET}")
            self.add_result("User-Agent Endpoint", self.test_user_agent_endpoint())
            
            print(f"{Colors.TESTER}[tester::#ROOT] Terminating program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#ROOT] Program terminated successfully{Colors.RESET}")
            self.stop_server()
            
            # File operation tests
            print(f"\n{Colors.TESTER_BOLD}[tester::#FILE] Running tests for File Operations{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#FILE] Running program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#FILE] $ ./build/server --directory {self.test_dir}{Colors.RESET}")
            
            self.start_server(with_directory=True)
            print(f"{Colors.PROGRAM}[your_program] [HttpServer] Listening on port 4221{Colors.RESET}")
            print(f"{Colors.PROGRAM}[your_program] Waiting for a client to connect...{Colors.RESET}")
            
            print(f"{Colors.TESTER}[tester::#FILE] Testing file serving{Colors.RESET}")
            self.add_result("File Serving", self.test_file_serving())
            
            print(f"{Colors.TESTER}[tester::#FILE] Testing file not found{Colors.RESET}")
            self.add_result("File Not Found", self.test_file_not_found())
            
            print(f"{Colors.TESTER}[tester::#FILE] Testing file creation{Colors.RESET}")
            self.add_result("File Creation", self.test_file_creation())
            
            print(f"{Colors.TESTER}[tester::#FILE] Testing large request body{Colors.RESET}")
            self.add_result("Large Request Body", self.test_large_request_body())
            
            print(f"{Colors.TESTER}[tester::#FILE] Testing empty request body{Colors.RESET}")
            self.add_result("Empty Request Body", self.test_empty_request_body())
            
            print(f"{Colors.TESTER}[tester::#FILE] Terminating program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#FILE] Program terminated successfully{Colors.RESET}")
            self.stop_server()
            
            # Concurrency tests
            print(f"\n{Colors.TESTER_BOLD}[tester::#CONC] Running tests for Concurrent Connections{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#CONC] Running program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#CONC] $ ./build/server{Colors.RESET}")
            
            self.start_server()
            print(f"{Colors.PROGRAM}[your_program] [HttpServer] Listening on port 4221{Colors.RESET}")
            print(f"{Colors.PROGRAM}[your_program] Waiting for a client to connect...{Colors.RESET}")
            
            print(f"{Colors.TESTER}[tester::#CONC] Creating multiple parallel connections{Colors.RESET}")
            self.add_result("Concurrent Connections", self.test_concurrent_connections())
            
            print(f"{Colors.TESTER}[tester::#CONC] Testing rapid sequential requests{Colors.RESET}")
            self.add_result("Rapid Sequential Requests", self.test_rapid_requests())
            
            print(f"{Colors.TESTER}[tester::#CONC] Terminating program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#CONC] Program terminated successfully{Colors.RESET}")
            self.stop_server()
            
            # Persistent connection tests
            print(f"\n{Colors.TESTER_BOLD}[tester::#PERSIST] Running tests for Persistent Connections{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#PERSIST] Running program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#PERSIST] $ ./build/server{Colors.RESET}")
            
            self.start_server()
            print(f"{Colors.PROGRAM}[your_program] [HttpServer] Listening on port 4221{Colors.RESET}")
            print(f"{Colors.PROGRAM}[your_program] Waiting for a client to connect...{Colors.RESET}")
            
            print(f"{Colors.TESTER}[tester::#PERSIST] Testing keep-alive connections{Colors.RESET}")
            self.add_result("Keep-Alive Connections", self.test_keep_alive_connections())
            
            print(f"{Colors.TESTER}[tester::#PERSIST] Testing connection close{Colors.RESET}")
            self.add_result("Connection Close", self.test_connection_close())
            
            print(f"{Colors.TESTER}[tester::#PERSIST] Terminating program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#PERSIST] Program terminated successfully{Colors.RESET}")
            self.stop_server()
            
            # Edge case tests
            print(f"\n{Colors.TESTER_BOLD}[tester::#EDGE] Running tests for Edge Cases{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#EDGE] Running program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#EDGE] $ ./build/server{Colors.RESET}")
            
            self.start_server()
            print(f"{Colors.PROGRAM}[your_program] [HttpServer] Listening on port 4221{Colors.RESET}")
            print(f"{Colors.PROGRAM}[your_program] Waiting for a client to connect...{Colors.RESET}")
            
            print(f"{Colors.TESTER}[tester::#EDGE] Testing special characters in path{Colors.RESET}")
            self.add_result("Special Characters in Path", self.test_special_characters_in_path())
            
            print(f"{Colors.TESTER}[tester::#EDGE] Terminating program{Colors.RESET}")
            print(f"{Colors.TESTER}[tester::#EDGE] Program terminated successfully{Colors.RESET}")
            self.stop_server()
            
        finally:
            self.cleanup()
        
        # Print summary
        self.print_summary()
        return all(result.passed for result in self.results)
    
    def print_summary(self):
        """Print test results summary"""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        failed = total - passed
        
        print(f"\n" + "=" * 50)
        print(f"📊 TEST SUMMARY")
        print(f"=" * 50)
        
        # Show individual test results
        for result in self.results:
            status = f"{Colors.SUCCESS}✅ PASS{Colors.RESET}" if result.passed else f"{Colors.ERROR}❌ FAIL{Colors.RESET}"
            print(f"{status} {result.name}")
            if result.message and not result.passed:
                print(f"      {Colors.ERROR}{result.message}{Colors.RESET}")
        
        print(f"\nResults: {passed}/{total} tests passed")
        
        if failed == 0:
            print(f"{Colors.SUCCESS}🎉 Test passed. Congrats!{Colors.RESET}")
            print(f"{Colors.SUCCESS}All {total} tests completed successfully.{Colors.RESET}")
        else:
            print(f"{Colors.ERROR}❌ Test failed!{Colors.RESET}")
            print(f"{Colors.ERROR}{failed} out of {total} tests failed.{Colors.RESET}")
            print(f"{Colors.ERROR}Please check the output above for details.{Colors.RESET}")

def main():
    tester = ServerTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()