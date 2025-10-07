import socket
import threading
import time

HOST = "0.0.0.0"
PORT = 5000

clients = []
players = {} 
board = []
current_turn = "w" 
game_started = False

def create_board():
    global board
    board = [[" " for _ in range(8)] for _ in range(8)]
    for row in range(3):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = "b"
    for row in range(5, 8):
        for col in range(8):
            if (row + col) % 2 == 1:
                board[row][col] = "w"

def print_board():
    s = "  a b c d e f g h\n"
    for i, row in enumerate(board):
        s += str(8-i) + " "
        s += " ".join(row)
        s += " " + str(8-i) + "\n"
    s += "  a b c d e f g h\n"
    return s

def parse_move(move):
    try:
        start, end = move.split()
        col_map = {"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}
        sr = 8 - int(start[1])
        sc = col_map[start[0]]
        er = 8 - int(end[1])
        ec = col_map[end[0]]
        return sr, sc, er, ec
    except:
        return None

def is_valid_move(player_color, sr, sc, er, ec):
    if not (0 <= sr < 8 and 0 <= sc < 8 and 0 <= er < 8 and 0 <= ec < 8):
        return False
    if board[sr][sc].lower() != player_color:
        return False
    if board[er][ec] != " ":
        return False
    
    dr = er - sr
    dc = ec - sc

    if abs(dr) == 1 and abs(dc) == 1:
        if player_color == "w" and dr == -1:
            return True
        if player_color == "b" and dr == 1:
            return True
        return False
        
    if abs(dr) == 2 and abs(dc) == 2:
        mid_r = sr + dr // 2
        mid_c = sc + dc // 2
        mid_piece = board[mid_r][mid_c].lower()
        if mid_piece != " " and mid_piece != player_color:
            return True
            # if player_color == "w" and dr == -2:
            #     return True
            # if player_color == "b" and dr == 2:
            #     return True
            
    return False

def make_move(sr, sc, er, ec):
    dr = er - sr
    dc = ec - sc

    if abs(dr) == 2 and abs(dc) == 2:
        mid_r = sr + dr // 2
        mid_c = sc + dc // 2
        board[mid_r][mid_c] = " "
    
    board[er][ec] = board[sr][sc]
    board[sr][sc] = " "
    return (abs(dr) == 2)

def has_more_captures(player_color, r, c):
    directions = [(-2, -2), (-2, 2), (2, -2), (2, 2)]
    for dr, dc in directions:
        er, ec = r + dr, c + dc
        mid_r, mid_c = r + dr // 2, c + dc // 2
        if 0 <= er < 8 and 0 <= ec < 8 and 0 <= mid_r < 8 and 0 <= mid_c < 8:
            if board[er][ec] == " ":
                mid_piece = board[mid_r][mid_c].lower()
                if mid_piece != " " and mid_piece != player_color:
                    return True
    return False

def broadcast(msg):
    for c in clients:
        try:
            c.send(msg.encode())
        except:
            pass

def handle_client(conn, addr):
    global clients, players, game_started, current_turn
    print(f"Игрок подключился: {addr}")
    clients.append(conn)

    if not game_started:
        conn.send(f"Ожидание второго игрока...\nПодключенные: {', '.join(str(a[0]) for a in [c.getpeername() for c in clients])}\n".encode())
        while len(clients) < 2:
            time.sleep(1)

    if conn not in players:
        color = "w" if len(players) == 0 else "b"
        players[conn] = color
        conn.send(f"Вы играете за: {color}\n".encode())

    if len(players) == 2 and not game_started:
        game_started = True
        broadcast("Оба игрока подключены! Игра начинается!\n")
        broadcast(print_board())
        broadcast(f"Сейчас ход: {current_turn}\n")

    while True:
        try:
            data = conn.recv(1024).decode().strip()
            if not data:
                break

            if players[conn] != current_turn:
                conn.send("Сейчас не ваш ход\n".encode())
                continue

            move = parse_move(data)
            if not move:
                conn.send("Неверный формат. Пример: a3 b4\n".encode())
                continue

            sr, sc, er, ec = move
            if is_valid_move(players[conn], sr, sc, er, ec):
                was_capture = make_move(sr, sc, er, ec)
                broadcast(print_board())

                if was_capture and has_more_captures(players[conn], er, ec):
                    conn.send("Вы можете сделать ещё один ход\n".encode())
                    continue
                
                current_turn = "b" if current_turn == "w" else "w"
                broadcast(f"Сейчас ход: {current_turn}\n")
            else:
                conn.send("Недопустимый ход\n".encode())

        except:
            break

    conn.close()
    clients.remove(conn)
    if conn in players:
        del players[conn]
    print(f"Игрок отключился: {addr}")

def main():
    create_board()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)
    print("Сервер запущен, ждём игроков...")

    try:
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()
            print("Подключенные игроки:", [c.getpeername()[0] for c in clients])
    except KeyboardInterrupt:
        print("\nОтключение сервера...")
    finally:
        server_socket.close()
        print("Сервер остановлен.")

if __name__ == "__main__":
    main()

