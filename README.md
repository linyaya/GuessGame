In GameServer.py, there are one thread for each client.
The main implemenation is in 'onClientThread' function

For state variable, there are 5 possible values:

1 stands for user authentication
In this while loop, it will continuously prompt user to input username and password until success.
'enter' is allowed, but will cause '4002'.
if not correct, will cause '1002'

2 stands for in the game hall
only allow /list, /enter command or it will send '4002'

22 stands for waiting for another player/in the waiting room
when the user is the first player who enters this room, create another thread called waitForPlayerThread.
This new thread is to check whether there is a new player in the room or not.
The parent thread is to get input from client.
The input could be the command for state 3, or an empty message(the msg client sends to server when it terminates interruptly)
An improvement in this part is that I assume there is no input from client, e.g. keyborad is dead.
Otherwise there will be no error warning but the input will be next command from client.

3 stands for playing a game
only allow /guess true, /guess false. othrewise will cause '4002'

33 stands for waiting for another guess
The client who first make a guess will generate a thread called waitForGuessThread.
This new thread is to check whether another player makes a guess or nor.
The parent thread is to get the input from client.
The input could be an empty message(the msg client sends to server when it terminates interruptly) or command for state 2
Also similar to state 22, no input in this waiting period.

except state 1, it's not allowed to just press 'enter', it will cause some error but haven't handled yet.