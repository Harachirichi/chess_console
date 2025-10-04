import socket

HOST = "0.0.0.0"  
PORT = 5000      

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen(1)

print("Ожидаем подключение...")
conn, addr = server_socket.accept()
print(f"Подключился клиент: {addr}")

while True:
    data = conn.recv(1024).decode()
    if not data:
        break
    print("Клиент:", data)
    msg = input("Сервер (ты): ")
    conn.send(msg.encode())

conn.close()
