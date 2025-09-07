#include <iostream>
#include <sys/types.h>
#include <sys/socket.h>
#include <unistd.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <string.h>
#include <string>

using namespace std;

int main(){

    // create a socket

    int listening = socket(AF_INET, SOCK_STREAM, 0);
    // AF_INET -> IPv4
    // SOCK_STREAM -> TCP
    // 0 -> IP protocol

    if (listening == -1){
        cerr << "Can't create a socket" << endl;
        return -1;
    }
    else{
        cout << "Socket created" << endl;
    }

    // bind the socket to ip/port

    sockaddr_in hint;  // struct that holds info about ipv4 address and port
    hint.sin_family = AF_INET;  // address family
    hint.sin_port = htons(54000); // port number (host to network short)
    inet_pton(AF_INET, "0.0.0.0", &hint.sin_addr);
    // presentation to network (convert IP address from text to binary form)
    // 0.0.0.0 -> bind to all available interfaces
    // &hint.sin_addr -> pointer to the struct where the binary form will be stored

    if(::bind(listening, (struct sockaddr*)&hint, sizeof(hint)) == -1){ // assigns a local address to the socket
        cerr << "Can't bind to IP/port" << endl;
        return -2;
    }
    else{
        cout << "Binded to IP/port" << endl;
    }

    sockaddr_in localAddr;
    socklen_t addrLen = sizeof(localAddr);
    if (getsockname(listening, (struct sockaddr*)&localAddr, &addrLen) == -1) {
        cerr << "Error getting local socket info" << endl;
    } else {
        char ipStr[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &localAddr.sin_addr, ipStr, sizeof(ipStr));
        cout << "Server running on " << ipStr << ":" << ntohs(localAddr.sin_port) << endl;
    }

    // mark the socket for listening in

    if(listen(listening, SOMAXCONN) == -1){ // SOMAXCONN -> maximum number of connections
        cerr << "Can't listen" << endl;
        return -3;
    }
    else{
        cout << "Listening..." << endl;
    }


    // accept a connection

    sockaddr_in client;
    socklen_t clientSize = sizeof(client);  // socklen_t -> type expected by accept() for size of address struct
    char host[NI_MAXHOST]; // buffer to store hostname of client
    char svc[NI_MAXSERV]; // buffer to store service (port number) the client is connected on

    int clientSocket = ::accept(listening, (sockaddr*)&client, &clientSize);

    if(clientSocket == -1){
        cerr << "Problem with client connecting"<<endl;
        return -4;
    }
    else{
        cout << "Client connected" << endl;
    }

    // close the listening socket

    close(listening);

    memset(host, 0, NI_MAXHOST); 
    memset(svc, 0, NI_MAXSERV);

    int result = getnameinfo((sockaddr*)&client, sizeof(client), host, NI_MAXHOST, svc, NI_MAXSERV, 0);
    // getnameinfo -> converts a socket address to a readable host ip and port string, fills the host and svc buffers

    if(result == 0){ // if non-zero, there was an error
        cout << host << " connected on " << svc << endl;
    } else { // if zero, success
        inet_ntop(AF_INET, &client.sin_addr, host, NI_MAXHOST); // convert binary IP address to a human readable string
        cout << host << " connected on " << ntohs(client.sin_port) << endl; // ntohs -> network to host short byte order 
    }
    

    // while receving- display message, echo message

    char buf[4096]; // buffer to hold received data
    while(true){
        
        memset(buf, 0, 4096);  // clear the buffer
        // buf -> pointer to the buffer
        // 0 -> value to set each byte to
        // 4096 -> number of bytes to set

        
        
        // wait for a message 
        int bytesReceived = recv(clientSocket, buf, 4096, 0);
        // recv -> receive data from a connected socket
        // clientSocket -> socket to receive data from
        // buf -> pointer to buffer to store received data
        // 4096 -> maximum number of bytes to read

        if(bytesReceived == -1){
            cerr << "Error in recv(). Quitting" << endl;
            break;
        }

        if(bytesReceived == 0){
            cout << "Client disconnected " << endl;
            break;
        }
        // display message
        cout << "Received " << bytesReceived << " bytes: " << string(buf, 0, bytesReceived) << endl;

        // resend message
        send(clientSocket, buf, bytesReceived + 1, 0);
        
    }

    // close the socket
    close(clientSocket);
    cout << "Socket closed" << endl;

    return 0;
}