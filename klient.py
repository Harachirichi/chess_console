import socket
import threading

HOST = "127.0.0.1"
PORT = 5000

my_color = None
my_turn = False

def receive_messages(sock):
    global my_turn, my_color
    while True:
        try:
            msg = sock.recv(4096).decode()
            if not msg:
                break

            print(msg, end="")

            if "Сейчас ход:" in msg:
                current = msg.strip().split(":")[-1].strip()
                my_turn = (current == my_color)
                if my_turn:
                    print("\nТвой ход: ", end="")

            if "Вы играете за:" in msg:
                my_color = msg.strip().split(":")[-1].strip()

        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))

    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    while True:
        try:
            if my_turn:
                user_input = input()
                if not user_input:
                    continue
                sock.send(user_input.encode())
        except KeyboardInterrupt:
            print("\nОтключение...")
            break
        except:
            break

    sock.close()

if __name__ == "__main__":
    main()

