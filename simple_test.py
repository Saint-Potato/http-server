#!/usr/bin/env python3
"""
Simple HTTP Server Test Script
Just the basics - no fancy features
"""

import socket
import subprocess
import time
import os
import tempfile

def test_server():
    print("=== Simple HTTP Server Tests ===\n")
    
    # Start server
    print("1. Starting server...")
    server = subprocess.Popen(['./build/server'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1)  # Give server time to start
    
    try:
        # Test 1: Basic connection
        print("2. Testing basic connection...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 4221))
        sock.send(b'GET / HTTP/1.1\r\nHost: localhost\r\n\r\n')
        response = sock.recv(1024).decode()
        sock.close()
        
        if '200 OK' in response:
            print("   ✓ GET / returns 200 OK")
        else:
            print("   ✗ GET / failed")
            print(f"   Response: {response}")
        
        # Test 2: Echo endpoint
        print("3. Testing echo endpoint...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 4221))
        sock.send(b'GET /echo/hello HTTP/1.1\r\nHost: localhost\r\n\r\n')
        response = sock.recv(1024).decode()
        sock.close()
        
        if '200 OK' in response and 'hello' in response:
            print("   ✓ GET /echo/hello works")
        else:
            print("   ✗ Echo endpoint failed")
            print(f"   Response: {response}")
        
        # Test 3: User-Agent
        print("4. Testing user-agent endpoint...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 4221))
        sock.send(b'GET /user-agent HTTP/1.1\r\nHost: localhost\r\nUser-Agent: test-client\r\n\r\n')
        response = sock.recv(1024).decode()
        sock.close()
        
        if '200 OK' in response and 'test-client' in response:
            print("   ✓ GET /user-agent works")
        else:
            print("   ✗ User-agent endpoint failed")
            print(f"   Response: {response}")
        
        # Test 4: 404
        print("5. Testing 404 response...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(('localhost', 4221))
        sock.send(b'GET /nonexistent HTTP/1.1\r\nHost: localhost\r\n\r\n')
        response = sock.recv(1024).decode()
        sock.close()
        
        if '404' in response:
            print("   ✓ GET /nonexistent returns 404")
        else:
            print("   ✗ 404 test failed")
            print(f"   Response: {response}")
        
        print("\n✓ Basic tests completed!")
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
    
    finally:
        # Stop server
        print("6. Stopping server...")
        server.terminate()
        server.wait()

if __name__ == "__main__":
    # Build first
    print("Building server...")
    result = os.system("cmake --build ./build")
    if result != 0:
        print("Build failed!")
        exit(1)
    
    test_server()