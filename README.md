# Basic TCP CHAT client server

badic tcp chat client server with 

## how to
    just run the server and you are good to go
    comands:
        MESSAGE : 'Send a private message to someone. Type '1 <destination clientname> - <content>',   
        BROADCAST : 'Send a message to the entire chat room. Type '2 <content>',
        MULTICAST: 'Send a message to some people. Type '3 <clientnames> <content>',          
        LOGOUT : 'Disconnect this session.',
        SHOWCLIENT : 'Display all chat memebers online',
        SHOWHISTORY : 'send all chat and login message betwhen client and server'
    login
    basic multi-theard
    plaintext storage

## Usage

```bash
python3 server.py
server is up

python3 client.py
welcome
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.