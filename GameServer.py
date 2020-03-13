#!/usr/bin/python3

import socket
import threading
import sys
import random
import distutils
from distutils import util
import multiprocessing

roomNum = 10

roomList = [None]*roomNum

userInfo = {}

incoMsg = '4002 Unrecognized message'



def main(argv):

    global roomNum
    global roomList
    global userInfo
    global incoMsg
    global threadList

    serverPort = int(argv[1])
 
    txtPath = argv[2]

    try:
        file = open(txtPath, 'r')
    except IOError as emsg:
        print("File open error: ", emsg)
        sys.exit(1)

    lines = file.readlines()
    for line in lines:
        userName, password = line.split(':')
        userInfo[userName.strip()] = password.strip()

    # create socket and bind
    try:
        gameServerSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        gameServerSocket.bind( ("", serverPort) )
    except socket.error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)
    
    gameServerSocket.listen(5)
    
    while True:
        # accept new connection
        try:
            client = gameServerSocket.accept()   
        except socket.error as emsg:
            print("Socket error: ", emsg)
            sys.exit(1)

        newthd = threading.Thread(target=oneClientThread, args=(client,))
        newthd.daemon = True
        newthd.start()
        
    gameServerSocket.close()

def waitForGuess(client, roomNo, lock):
    global roomList

    connectionSocket, addr = client

    while True:
        lock.acquire()

        if roomList[int(roomNo)-1] == []:

            try:
                sendMsg = '3021 You are the winner'
                connectionSocket.send(sendMsg.encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                lock.release()
                break
            lock.release()
            break

        elif len(roomList[int(roomNo)-1]) == 5:

            subState = roomList[int(roomNo)-1][4]
            if subState == '3023':
                sendMsg = '3023 The result is a tie'
            elif subState == '3021':
                sendMsg = '3021 You are the winner'
            elif subState == '3022':
                sendMsg = '3022 You lost this game'

            roomList[int(roomNo)-1] = []
            try:
                connectionSocket.send(sendMsg.encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                lock.release()
                break
            lock.release()
            break
        lock.release()

def waitForPlayer(client, roomNo, lock):

    connectionSocket, addr = client
    while True:
        lock.acquire()
        if len(roomList[int(roomNo)-1]) == 2:
            sendMsg = '3012 Game started. Please guess true or false'
            try:
                connectionSocket.send(sendMsg.encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                lock.release()
                break
            lock.release()
            break
        lock.release()

    
def oneClientThread(client):

    global roomNum
    global roomList
    global userInfo
    global incoMsg


    connectionSocket, addr = client

    # state 1: user authentication
    # state 2: in the game hall
    # state 22: wait for another player
    # state 3: playing a game
    # state 33: wait for another guess

    state = 1

    while state == 1:
        try:
            msg = connectionSocket.recv(4096)
        except socket.error as emsg:
            print("Socket error: ", emsg)
            break
        if not msg:
            print("client: ", addr, " terminated")
            break
        try:
            _, userName, password = msg.decode().split()
        except Exception as emsg:
            print(emsg)
            connectionSocket.send(incoMsg.encode())
            continue

        if userInfo.get(userName) == password:
            sendMsg = '1001 Authentication successful'
            try:
                connectionSocket.send(sendMsg.encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                break
            state = 2
        else:
            try:
                sendMsg = '1002 Authentication failed'
                connectionSocket.send(sendMsg.encode())
            except socket.error as emsg:
                print("Socket error: ", emsg)
                break

    lock = threading.Lock()

    roomNo = 1

    while state != 1:

        try:
            msg = connectionSocket.recv(4096)
        except socket.error as emsg:
            print("Socket error: ", emsg)
            roomList[int(roomNo)-1] = []
            break

        if not msg:
            print("client: ", addr, " terminated")
            roomList[int(roomNo)-1] = []
            break

        if state == 22:
            state = 3
        if state == 33:
            state = 2

        if state == 2:

            try:
                command = msg.decode().split()[0]
                command = command.strip()
            except Exception as emsg:
                print(emsg)
                connectionSocket.send(incoMsg.encode())
                continue

            if command == '/list':
                if lock.acquire(1):
                    sendMsg = '3001 ' + str(roomNum)
                    for i in range(roomNum):
                        if roomList[i] == None:
                            playerNum = 0
                        elif len(roomList[i]) >= 2:
                            playerNum = 2
                        else:
                            playerNum = len(roomList[i])
                        sendMsg = sendMsg + ' ' + str(playerNum)
                    try:
                        connectionSocket.send(sendMsg.encode())
                    except socket.error as emsg:
                        print("Socket error: ", emsg)
                        break
                    lock.release()
            elif command == '/enter':
                try:
                    _, roomNo = msg.decode().split()
                    roomNo = roomNo.strip()
                    if lock.acquire(1):
                        thisRoomList = roomList[int(roomNo)-1]
                        lock.release()
                except Exception as emsg:
                    connectionSocket.send(incoMsg.encode())
                    print("error: ", emsg)
                    continue
                if lock.acquire(1):
                    currentPlayerNum = 0 if thisRoomList == None else len(thisRoomList)
                    if currentPlayerNum == 0:
                        roomList[int(roomNo)-1] = [userName]
                        sendMsg = '3011 Wait'
                        state = 22
                        waitForPlayerThread = threading.Thread(target=waitForPlayer, args=(client,roomNo,lock,))
                        waitForPlayerThread.daemon = True
                        waitForPlayerThread.start()

                    elif currentPlayerNum >= 2:
                        sendMsg = '3013 The room is full'
                    elif currentPlayerNum == 1:
                        roomList[int(roomNo)-1].append(userName)
                        sendMsg = '3012 Game started. Please guess true or false'
                        state = 3
                    try:
                        connectionSocket.send(sendMsg.encode())
                    except socket.error as emsg:
                        print("Socket error: ", emsg)
                        break
                    lock.release()
            elif command == '/exit':
                sendMsg = '4001 Bye bye'
                try:
                    connectionSocket.send(sendMsg.encode())
                except socket.error as emsg:
                    print("Socket error: ", emsg)
                break
            else:
                try:
                    connectionSocket.send(incoMsg.encode())
                except socket.error as emsg:
                    print("Socket error: ", emsg)


        elif state == 3:

            if lock.acquire(1):
                if userName not in roomList[int(roomNo)-1]:
                    try:
                        sendMsg = '3021 You are the winner'
                        connectionSocket.send(sendMsg.encode())
                    except socket.error as emsg:
                        print("Socket error: ", emsg, addr)
                        break
                    state = 2
                lock.release()

            if state == 2:
                continue

            try:
                command, booleanStr = msg.decode().split()
                command = command.strip()
                if booleanStr.strip() == 'true':
                    boolean = True
                elif booleanStr.strip() == 'false':
                    boolean = False
                else:
                    connectionSocket.send(incoMsg.encode())
                    continue
            except Exception as emsg:
                connectionSocket.send(incoMsg.encode())
                print(emsg)
                continue

            if command == '/guess':

                if lock.acquire(1):
                   
                    roomList[int(roomNo)-1].append(boolean)
                    thisRoomList = roomList[int(roomNo)-1]
                    if len(thisRoomList) == 4:
                        if thisRoomList[2] == thisRoomList[3]:
                            roomList[int(roomNo)-1].append('3023')
                            sendMsg = '3023 The result is a tie'
                        else:
                            random_bit = random.getrandbits(1)
                            r = bool(random_bit)
                            if r == boolean:
                                roomList[int(roomNo)-1].append('3022')
                                sendMsg = '3021 You are the winner'
                            else:
                                roomList[int(roomNo)-1].append('3021')
                                sendMsg = '3022 You lost this game'

                        state = 2

                        try:
                            connectionSocket.send(sendMsg.encode())
                        except socket.error as emsg:
                            print("Socket error: ", emsg)
                            break

                    elif len(thisRoomList) == 3:

                        state = 33
                        waitForGuessThread = threading.Thread(target=waitForGuess, args=(client,roomNo,lock,))
                        waitForGuessThread.daemon = True
                        waitForGuessThread.start()
                       
                    lock.release()

            else:
                try:
                    connectionSocket.send(incoMsg.encode())
                except socket.error as emsg:
                    print("Socket error: ", emsg)
                    roomList[int(roomNo)-1] = []
                    break

    connectionSocket.close()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python3 GameServer.py <Server_port> <UserInfo.txt path>")
        sys.exit(1)
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        roomList = [None] * roomNum
        sys.exit(1)