import socket

HOST = "127.0.0.1" 
PORT = 5000

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))
print("Подключились к серверу")

while True:
    msg = input("Клиент (ты): ")
    client_socket.send(msg.encode())
    data = client_socket.recv(1024).decode()
    print("Сервер:", data)

client_socket.close()
