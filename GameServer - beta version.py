# Name = Lau Cheuk Ning, UID = 3035745051
#!/usr/bin/python3


from concurrent.futures import thread
import socket
import os.path
import sys
import random
import threading

USER_INFO = {}
Commandmsg =   {1001: "Authentication successful",
                1002: "Authentication failed",
                3001: "",
                3011: "Wait",
                3012: "Game started. Please guess true or false",
                3013: "The room is full",
                3021: "You are the winner",
                3022: "You lost this game",
                3023: "The result is a tie",
                4001: "Bye bye",
                4002: "Unrecognized message"
                }



class JoinRoom(object):
    def __init__(self, id):
        self.id = id
        self.playerGuess = {}
        self.booleanValue = -1
    
    def restart(self):
        self.__init__(self.id)

    def GenerateBooleanValue(self):
        if self.booleanValue == -1:
            self.booleanValue = random.randint(0, 1)        

    def player(self, playerJoined):
        self.playerGuess[playerJoined] = -1

    def secondPlayer(self, playerJoined):
        for ppl in self.playerGuess:
            if ppl != playerJoined:
                return ppl
        return None

    def checkWinner(self, playerJoined):
        self.GenerateBooleanValue()
        SecondPlayerGuess = self.playerGuess[self.secondPlayer(playerJoined)]

        if SecondPlayerGuess == -1 :  # not yet have second player 
            return -1
        FirstPlayerGuess = self.playerGuess[playerJoined]
        if FirstPlayerGuess == SecondPlayerGuess:
            return 2                # tie
        if self.booleanValue == FirstPlayerGuess:
            return 1
        if self.booleanValue != FirstPlayerGuess:
            return 0



#room number and status of player
class Player(object):
    def __init__(self, name):
        self.name = name        
        self.initStatus()
    
    def initStatus(self):
        self.roomNumber = 0
        self.playerStatus = 0
        self.sockfd = None
        self.player2Status = False

    def login(self, sockfd):
        self.playerstatus = 1
        self.sockfd = sockfd

    def enterRoom(self, roomNumber):
        self.roomNumber = roomNumber
        self.playerstatus = 2

    def FinishGame(self):
        self.roomNumber = -1
        self.playerstatus = 1


class GamePlay(object):
    def __init__(self, sockser):
        self.lock = threading.Lock()
        self.sockser = sockser
        self.gameRoom = [JoinRoom(id) for id in range(10)]
        self.players = [Player(name) for name in USER_INFO]

    def GameStart(self):
        while True:
            client = self.sockser.accept()
            moreClient = threading.Thread(target = self.ClientAuthentication, args = (client,))
            moreClient.start()


    def msgRcv(self,sockfd, msg):
        try:
            line = sockfd.recv(1024).decode().split()
        except socket.error as emsg:
            print("Socket recv error: ", emsg)
            return 0

        msg[:] = list(line)
        return 1

    def msgSend(self, sockfd, command):
        msg = str(command)+" "+Commandmsg[command]
        if command == 3001:
            with self.lock:
                msg +=  str(10) + " " + " ".join([str(len(room.playerGuess)) for room in self.gameRoom])
        try:
            sockfd.send(msg.encode())
        except socket.error as emsg:
            print("Socket send error: ", emsg)
            return False
        return True

    # check connection of two players 
    def ConnectionCheck(self, connection, player1, sockfd, msg):
        if connection and len(msg) > 0 :
            return True
        if not player1:
            sockfd.close()
            return False
        if player1.playerstatus == 3:
            with self.lock:
                CurrentRoom = self.gameRoom[player1.roomNumber]
                player2 = CurrentRoom.secondPlayer(player1)
            if player2:
                self.msgSend(player2.sockfd,3021)
                if CurrentRoom.playerGuess[player2] == 2:
                    player2.player2Status = True
                player2.FinishGame()
        if player1.playerstatus > 1:
            with self.lock:
                self.gameRoom[player1.roomNumber].restart()
        player1.initStatus()
        return False


    # for handle the client meg for authentication
    def ClientAuthentication(self, client):
        sockfd, a = client

        client_INFO = []
        connection = self.msgRcv(sockfd, client_INFO)
        if not self.ConnectionCheck(connection,None,sockfd,client_INFO):
            return
        
        while client_INFO[1] not in USER_INFO or USER_INFO[client_INFO[1]] != client_INFO[2]:
            connection = self.msgSend(sockfd, 1002)
            connection &= self.msgRcv(sockfd, client_INFO)
            if not self.ConnectionCheck(connection,None,sockfd,client_INFO):
                return
            
        for player in self.players:
            if player.name == client_INFO[1]:
                CurrentPlayer = player
            
        CurrentPlayer.login(sockfd)
        connection = self.msgSend(sockfd,1001)

        #Starting of the game
        while(CurrentPlayer.playerstatus != 0):
            msg = []
            connection &= self.msgRcv(sockfd,msg)
            if not self.ConnectionCheck(connection,CurrentPlayer,sockfd,msg):
                return
            command = self.CommandHandle(msg, CurrentPlayer)
            print(command)
            if command:
                connection = self.msgSend(sockfd,command)
        
        sockfd.close


    def CommandHandle(self,msg,CurrentPlayer):
        status = CurrentPlayer.playerstatus
        CurrentRoomNumber = CurrentPlayer.roomNumber        
        #connect player2 = True
        command = 4002

        if CurrentPlayer.player2Status:
            CurrentPlayer.player2Status = False
        
        if(msg[0] == "/list" and len(msg) == 1):
            command = 3001
        
        
        elif(msg[0] == "/enter" and len(msg) == 2 and status == 1):
            try:
                roomNumber = int(msg[1]) - 1
            except:
                return command
            if roomNumber < 0 or roomNumber > 10:
                return command
        
            #check number of player in room
            self.lock.acquire()
            TargetRoom = self.gameRoom[roomNumber]
            NoOfPlayer = len(TargetRoom.playerGuess)

            if NoOfPlayer < 2 :
                CurrentPlayer.enterRoom(roomNumber)
                TargetRoom.player(CurrentPlayer)
            if NoOfPlayer == 1:
                player2 = TargetRoom.secondPlayer(CurrentPlayer)
                player2.playerstatus = 3
                CurrentPlayer.playerstatus = 3
                if not self.msgSend(player2.sockfd, 3012):
                    self.lock.release()
                    return None
                
            self.lock.release()
            command = NoOfPlayer + 3011
        
        elif (msg[0] == "/guess" and len(msg) == 2 and status == 3):
            #print(msg[1],status)
            if (msg[1] not in ["true", "false"]):
                return command

            self.lock.acquire()
            CurrentRoom = self.gameRoom[CurrentRoomNumber]            
            CurrentRoom.playerGuess[CurrentPlayer] = int(msg[1] == "true")
            player2 = CurrentRoom.secondPlayer(CurrentPlayer)
            if not player2:
                self.lock.release()
                return None
            result = CurrentRoom.checkWinner(CurrentPlayer)

            if result == -1 or not self.msgSend(player2.sockfd, 3021+result):
                self.lock.release()
                return None
            if result == 2:
                command = 3023
            else:
                print(result)
                command = 3022 - result

            CurrentRoom.restart()
            self.lock.release()
            CurrentPlayer.FinishGame()
            player2.FinishGame() 

        elif msg[0] == "/exit" and len(msg) == 1 and status == 1:
            CurrentPlayer.initStatus()
            command = 4001
        #print(msg[1],status)
        return command

# main function
def main(argv):
    global USER_INFO
    com, port, filepath = argv
    port = int(port)

    with open(filepath) as file:
        for text in file:
            Info = text.rstrip('\n').split(':')
            USER_INFO[Info[0]] = Info[1]   

    # create socket and bind
    sockser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sockser.bind(("",port))
    except  socket.error as err:
        print("error: ", err)
        sys.exit(1)

    # limit the number of player to 20
    sockser.listen(20)

    StartGame = GamePlay(sockser)
    StartGame.GameStart()
 

    sockser.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameServer.py <server_port> <path_to_user_file>")
        sys.exit(1)
    main(sys.argv)