import socket
import os.path
import sys

def main(argv):

	# create socket and connect to server
	try:
		clientSocket = socket.socket()
		clientSocket.connect((argv[1], int(argv[2])))
	except socket.error as emsg:
		print("Socket error: ", emsg)
		sys.exit(1)

	resCode = None

	while resCode != '1001':
		userName = input("Please input your user name:")
		password = input("Please input your password:")
		msg = '/login' + ' ' + userName.strip() + ' ' + password.strip()
		try:
			clientSocket.send(msg.encode())
		except socket.error as emsg:
			print("Socket error: ", emsg)
		try:
			response = clientSocket.recv(4096).decode()
		except socket.error as emsg:
			print("Socket error: ", emsg)

		if not response:
			print("server is broken")
			resCode = 'skip'
			break

		resCode = response.split()[0]
		print(response)


	while resCode != '4001' and resCode != 'skip':

		if resCode == '3011':
			try:
				response = clientSocket.recv(4096).decode()
			except socket.error as emsg:
				print("Socket error: ", emsg)

			if not response:
				print("server thread is broken")
				break

		else:
			msg = input()
			msg = msg.strip()
			try:
				clientSocket.send(msg.encode())
			except socket.error as emsg:
				print("Socket error: ", emsg)
			try:
				response = clientSocket.recv(4096).decode()
			except socket.error as emsg:
				print("Socket error: ", emsg)

			if not response:
				print("server thread is broken")
				break


		resCode = response.split()[0]
		print(response)

	print('Client ends')

	clientSocket.close()

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("Usage: python3 GameClient.py <Server_addr> <Server_port>")
		sys.exit(1)
	try:
		main(sys.argv)
	except KeyboardInterrupt:
		print("client terminated")