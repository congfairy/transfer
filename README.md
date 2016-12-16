# transfer

The files:
main.cpp:the c++ interface to run the client.
client.h:The head file of client.cpp.
client.cpp:It is the interface of the client from python to c++.
client.py:It is the fulfill of the client function.
libclient.so:the lib that is needed by main function.
server.py:the server code.

How to run:
The server:python3 server.py
The client:g++ -shared -fPIC -o libclient.so client.cpp -I/root/Python-3.5.0/Include/ -lpython3.5m -L/usr/local/lib/
           g++ main.cpp -o main -I/root/Python-3.5.0/Include/ -lpython3.5m ./libclient.so
           ./main
