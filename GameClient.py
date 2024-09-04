# Name = Lau Cheuk Ning, UID = 3035745051
#!/usr/bin/python3


import socket
import os.path
import sys


def main(argv):
    try:
        #create socket
        sockfd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockfd.connect((argv[1], int(argv[2])))
    except socket.error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)
		
    CheckLogin = False

    #stage of user authentication
    while not CheckLogin:
        user_name = input("Please input your user name:\n")
        password = input("Please input your password:\n")
        
        #check user input
        if len(user_name) < 1 or len(password) < 1:
            print("You have not input username or password, please input it again") 
            CheckLogin = False
        else:
            #send message to server
            try:
                sockfd.send((f"/login {user_name} {password}").encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                sys.exit(1)

            #receive message from the server
            try:
                msg = sockfd.recv(1024).decode()
                print(msg)
                msg = msg.split()
            except socket.error as emsg:
                print("Socket error: ", emsg)
                sys.exit(1)

            #authentication
            if msg[0] == "1001":
                CheckLogin = True
            elif msg[0] == "1002":
                CheckLogin = False

    #After successful authentication
    while CheckLogin:
        command = input()

        #send command to server
        try:
            sockfd.send(command.encode())
        except socket.error as emsg:
            print("Socket error: ", emsg)
            sys.exit(1)    

        #receive message from the server
        try:
            msg = sockfd.recv(1024).decode()
            print(msg)
            msg = msg.split()
        except socket.error as emsg:
            print("Socket error: ", emsg)
            sys.exit(1)

        if msg[0] == "4001":
            break

        #Waiting
        elif msg[0] == "3011":
            try:
                msg = sockfd.recv(1024).decode()
                print(msg)
                msg = msg.split()
            except socket.error as emsg:
                print("Socket error: ", emsg)
                sys.exit(1)
            
        #full
        elif msg[0] == "3013":
            try:
                msg = sockfd.recv(1024).decode()
                print(msg)
                msg = msg.split()
            except socket.error as emsg:
                print("Socket error: ", emsg)
                sys.exit(1)

    print("Client ends")
    sockfd.close()


if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("Usage: python3 GameClient.py <Server_addr> <Server_port> <filename>")
		sys.exit(1)
	main(sys.argv)