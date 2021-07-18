from socket import *
from threading import *
import logging
import datetime 
import os
from sys import stdout
from time import sleep

logging.basicConfig(level=logging.INFO, filename='chatserver.log', format='[%(levelname)s] %(asctime)s %(threadName)s %(message)s', ) 

#INIT
srv_address = 'localhost'
srv_port = 42069
buffer_size = 8192
block_time = 60    
time_expire = 30 * 60

clients = []                                  
past_connections = {}               
blocked_connections = {}         

#COMMANDS 

SHOWCLIENT = 'showclient'
BROADCAST = 'broadcast' 
MULTICAST = 'multicast'
MESSAGE = 'message'
LOGOUT = 'logout' 
SHOWHISTORY = 'showhistory'

commands_dict = {
    MESSAGE : 'Send a private message to someone. Type \'1 <destination clientname> - <content>\' ',   
    BROADCAST : 'Send a message to the entire chat room. Type \'2 <content>\'',
    MULTICAST: 'Send a message to some people. Type \'3 <clientnames> <content>\'',          
    LOGOUT : 'Disconnect this session.',
    SHOWCLIENT : 'Display all chat memebers online',
    SHOWHISTORY : 'send all past msg betwhen client and others'
}
# -------------------------------------------------
def search_string_in_file(file_name, string_to_search):

    line_number = 0
    list_of_results = []
    with open(file_name, 'r') as read_obj:
        for line in read_obj:
            line_number += 1
            if string_to_search in line:
                list_of_results.append((line_number, line.rstrip()))
    return list_of_results

def show_history(client,username):
    try:
        client_history = search_string_in_file('chatserver.log',username)
        for each in client_history:
            client.sendall((each[1]+'\n').encode())
    except:
        client.sendall('failed to catch'.encode())
        

# -------------------------------------------------

def show_clients(client, sender_username):
    other_clients = 'Users currently logged in: '
    
    for user in clients:
        if (user[0] != sender_username):
            other_clients += user[0] + ' '
    
    if (len(clients) < 2):     #If no client is online 
        other_clients += '[none] '
    
    client.sendall(other_clients.encode())

#BC
def broadcast(user, command):
    message = 'Braodcast message from ' + user + ': '

    try:
        for word in command[1:]:
            message += word + ' '        #Broadcasts to all Users
    except:
        client.sendall('wrong input(use this format [comand num , msg])'.encode())

    for user_tuple in clients:
        user_tuple[1].sendall(message.encode())

#MC
def multicast(sender_username, client, command):
    message = 'Multicast message from ' + sender_username + ': '
    dashsep = command.split('-')
    receivers = dashsep[0].split()
    msg = dashsep[1].split()

    for receiver in dashsep[1:]:
        try:

            for word in msg[0:]:
                message += word + ' '

            receiver_is_logged_in = False
            for user_tuple in clients:
                if user_tuple[0] == receiver:
                    user_tuple[1].sendall(message.encode())       #Send Message to a private user
                    receiver_is_logged_in = True
            
            if (not receiver_is_logged_in):
                client.sendall((receiver + ' is not logged in. ').encode())   #If user is not online'
            
        except:
            client.sendall('wrong input(use this format [comand num , user you want to send , msg])'.encode())

#PV
def private_message(sender_username, client, command):

    message = 'Private message from ' + sender_username + ': '

    try:
        receiver = command[1]
        
        for word in command[2:]:
            message += word + ' '

        receiver_is_logged_in = False
        for user_tuple in clients:
            if user_tuple[0] == receiver:
                user_tuple[1].sendall(message.encode())       #Send Message to a private user
                receiver_is_logged_in = True
        
        if (not receiver_is_logged_in):
            client.sendall((receiver + ' is not logged in. ').encode())   #If user is not online
    except:
        client.sendall('wrong input(use this format [comand num , user you want to send , msg])'.encode())


# ---------------------LOGOff---------------------
def logout(client):
    client.sendall('Good bye!'.encode())
    sleep(1)
    client.close() 

def client_exit(client, client_ip):
    for user in clients:
        if user[1] == client:
            clients.remove(user)
    print ('Client on %s : %s disconnected' %(client_ip, client))
    logging.info("Client on IP {} & Port {} Disconnected".format(client_ip, client))
    open("./user_pass.txt", 'w').close() 
    stdout.flush()     
    sleep(1)    
    client.close()

#TIMEOUT FUNCTION

def client_timeout(client, client_identifier):
    client.sendall('Your session has been ended due to inactivity. '.encode())    #If not active for 30 minutes, end session
    sleep(1)    
    client.close()
# -------------------------------------------------

def send_commands(client, client_ip_and_port, username):    
    while 1:
        try:
            client.sendall('\nEnter the number command:\n 1. Message\n 2. Broadcast\n 3. MultiCast \n 4. showClients\n 5. history\n 6. Logout\n'.encode())
            
            timeout_countdown = Timer(time_expire, client_timeout, (client, client_ip_and_port))     #Start Timeout_timer
            timeout_countdown.start()
            recvived = client.recv(buffer_size).decode()
            command = recvived.split()
            timeout_countdown.cancel() 
            past_connections[username] = datetime.datetime.now() 
            logging.log(1,"Client on IP {} & Port {} by user {} Sent {}".format(client_ip_and_port, client ,username , command))
        except:                                                     
            logout(client)
            client.close()
        
        if (command[0] == "1"):
            private_message(username, client, command)

        elif (command[0] == "2"):                                   
            broadcast(username, command)

        elif (command[0] == "3"):                                   
            multicast(username, client ,recvived)

        elif (command[0] == "4"):
            show_clients(client, username)

        elif (command[0] == "5"):
            show_history(client,username)    

        elif (command[0] == "6"):
            logout(client)
            
        else:
            client.sendall('Command not found. '.encode())

def login(client, username):
    client.sendall('\nLogin successful. Welcome!'.encode())
    clients.append((username, client))                              
    past_connections[username] = datetime.datetime.now() 

def is_already_logged_in(username):
    for user in clients:
        if user[0] == username:
            return True
    return False

# BLOCK
def block(ip_addr, client_sock, username):    
    list_of_blocked_usernames = blocked_connections[ip_addr]
    list_of_blocked_usernames.append(username)                             
    blocked_connections[ip_addr] = list_of_blocked_usernames
    client_sock.close()

def unblock(ip_addr, username):
    list_of_blocked_usernames = blocked_connections[ip_addr]
    list_of_blocked_usernames.remove(username)                              
    blocked_connections[ip_addr] = list_of_blocked_usernames


def is_blocked(ip_addr, username):
    list_of_blocked_usernames = blocked_connections[ip_addr]
    if (username in list_of_blocked_usernames):
        return True
    return False


def send_login(client_sock, client_ip):
    username = 'default'
    try:
        while (not username in logins):
            client_sock.sendall('\nPlease enter a valid username. '.encode())
            username = client_sock.recv(buffer_size).decode()  
        
            if (is_blocked(client_ip, username)):                               #Check if Blocked
                client_sock.sendall('Your access is temporarily blocked.'.encode())
                username = 'default'
            
            if (is_already_logged_in(username)):
                client_sock.sendall('This user has already logged in.'.encode())         #Check is user is logged in
                username = 'default'
        
        login_attempt_count = 0

        while login_attempt_count < 3:                                          #If login < 3 continue
            client_sock.sendall('Please enter your password. '.encode())
            password = client_sock.recv(buffer_size).decode()  
            
            if (logins[username] != password):
                login_attempt_count += 1
                client_sock.sendall('Wrong Username or Password. Please try again. '.encode())
            
            elif (logins[username]) and (logins[username] == password):
                login(client_sock, username)
                return (True, username)

        return (False, username)

    except:
        print("failed to login")
        return (False, username)


def send_create_username(client_sock):
    client_sock.sendall('Welcome! Would you like to create a new user? [yes/no]'.encode())
    response = client_sock.recv(buffer_size).decode()
    if (response == "yes"):

        created_username = False
        new_user = ""
        while (not created_username):
            client_sock.sendall('Please choose a username. '.encode())
            new_user = client_sock.recv(buffer_size).decode() 
            
            if (len(new_user) < 3 or len(new_user) > 8):
                client_sock.sendall('Usernames must be between 3 and 8 characters long. '.encode())    
            
            elif (new_user in logins):
                client_sock.sendall('This username already exists! Please choose another!'.encode())
            else:
                created_username = True
        
        new_pass = ""
        created_password = False
        while (not created_password):
            client_sock.sendall('Please type in a secure password. '.encode())
            new_pass = client_sock.recv(buffer_size).decode() 
            
            if (len(new_pass) < 4 or len(new_pass) > 18):
                client_sock.sendall('Passwords must be between 4 and 16 characters long.'.encode())  #PASSWORD ENTER
            else:
                created_password = True
        
        with open('./user_pass.txt', 'a') as aFile:
            usps = ('\n' + new_user+ ' ' + new_pass)
            aFile.write(usps)
        
        logins[new_user] = new_pass
        
        client_sock.sendall('New user created.\n'.encode())

    client_sock.sendall('okay, go for login\n'.encode())


# -------------------------------------------------

class ClientHandler(Thread):
    def __init__(self, Csock, addr):
        self.sock = Csock
        self.address = addr
        # self.username = username
        # clients.append(self)

        super().__init__()
        self.start()
    
    def run(self):
        
        if (self.address not in blocked_connections):
            blocked_connections[self.address] = []
        
        send_create_username(self.sock )
        
        try:
            while 1:
                user_login = send_login(self.sock , self.address)
                logging.info("User Login Info = {}".format(user_login))

                if (user_login[0]):                                                         #If login succeeds
                    send_commands(self.sock , self.address, user_login[1])
                else: 
                    self.sock .sendall('Login failed too many times. Please try after 60 seconds'.encode()) #If login fails
                    block(self.address, self.sock , user_login[1])
                    Timer(block_time, unblock, (self.address, user_login[1])).start()

        except:
            client_exit(self.sock , self.address) 

               
def populate_logins_dictionaries():
    user_logins = {}

    with open('./user_pass.txt') as aFile:
        for line in aFile:
            (key, val) = line.split()
            user_logins[key] = val

    return user_logins

logins = populate_logins_dictionaries()

Ssock = socket(AF_INET, SOCK_STREAM)
Ssock.bind( (srv_address, srv_port) )
Ssock.listen(5)
print('Server is Up!')


while True:
    Csock, addr = Ssock.accept()
    # username = Csock.recv(buffer_size).decode()
    client = ClientHandler(Csock, addr) #, username)