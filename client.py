from socket import *
from time import sleep
from threading import *
import logging

#INIT
srv_address = 'localhost'
srv_port = 42070
buffer_size = 8192

class ListenThread(Thread):
    def __init__(self, sock):
        self.sock = sock
        super().__init__()
        self.start()

    def run(self):
        print('Now listening!')
        while True:
            print( self.sock.recv(buffer_size).decode() )

# username = input('Enter your username: ')

logging.basicConfig(level=logging.INFO, filename='chatclient.log', format='[%(levelname)s] %(asctime)s %(threadName)s %(message)s',) 

while True:
    try:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect( (srv_address, srv_port) )
        print('Connected to {} on port {}'.format(srv_address, srv_port))
        logging.info("Unable to connect to the server!")
        
        # sock.send(username.encode())
        listener = ListenThread(sock)
        break
    except:
        print('Unable to connect to the server!\nRetrying in 5 seconds...')
        logging.info("Unable to connect to the server!")
        sleep(5)

while True:
    message = input()
    sock.send(message.encode())
