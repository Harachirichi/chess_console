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
last_capture_pos = None

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
    
def has_any_capture(player_color):
    for r in range(8):
        for c in range(8):
            if board[r][c].lower() == player_color:
                if has_more_captures(player_color, r, c):
                    return True
    return False

def is_valid_move(player_color, sr, sc, er, ec):
    global last_capture_pos
    print(f"Проверка хода: {sr},{sc} -> {er},{ec}, игрок: {player_color}")
    print(f"last_capture_pos: {last_capture_pos}")

    if not (0 <= sr < 8 and 0 <= sc < 8 and 0 <= er < 8 and 0 <= ec < 8):
        print("Неверные координаты")  
        return False
    if last_capture_pos is not None and (sr, sc) != last_capture_pos:
        print(f"Не продолжение серии ударов. Ожидается ход с {last_capture_pos}")
        return False
    if board[sr][sc].lower() != player_color:
        print(f"Не своя фигура: {board[sr][sc]}")
        return False
    if board[er][ec] != " ":
        print("Клетка назначения не пуста")
        return False
    
    piece = board[sr][sc]
    
    dr = er - sr
    dc = ec - sc
    print(f"dr={dr}, dc={dc}")

    if abs(dr) != abs(dc):
        print("Не диагональ")
        return False

    # ======== QUEEN =========
    if piece.isupper():  
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1

        enemy_count = 0
        enemy_pos = None

        r, c = sr + step_r, sc + step_c
        while r != er and c != ec:
            if board[r][c] != " ":
                if board[r][c].lower() == player_color:
                    return False
                if enemy_count >=1:
                    return False
                
                enemy_count += 1
                enemy_pos = (r, c)
            r += step_r
            c += step_c

        if enemy_count == 0:
            return True
        elif enemy_count == 1 and enemy_pos:
            expected_er = enemy_pos[0] + step_r
            expected_ec = enemy_pos[1] + step_c
            return er == expected_er and ec == expected_ec
    
    # ======== REGULAR CHECKER =========
    else:
        if abs(dr) == 1 and abs(dc) == 1:
            if has_any_capture(player_color):
                print("Запрещен обычный ход при возможности взятия")
                return False
            if player_color == "w" and dr == -1:
                return True
            if player_color == "b" and dr == 1:
                return True
            print("Неверное направление для обычного хода")
            return False
            
        elif abs(dr) == 2 and abs(dc) == 2:
            mid_r = sr + dr // 2
            mid_c = sc + dc // 2
            print(f"Промежуточная клетка: {mid_r},{mid_c}") 
            print(f"Промежуточная фигура: '{board[mid_r][mid_c]}'")  
            
            mid_piece = board[mid_r][mid_c]
            if mid_piece != " " and mid_piece.lower() != player_color:
                print("Взятие допустимо!")
                return True
            else:
                print(f"Недопустимая промежуточная фигура: '{mid_piece}'")
    print("Ход не прошел ни одну проверку")
    return False

def make_move(sr, sc, er, ec):
    piece = board[sr][sc]
    dr = er - sr
    dc = ec - sc
    was_capture = False
    captured_positions = []

    # ======== QUEEN =========
    if piece.isupper():  
        step_r = 1 if dr > 0 else -1
        step_c = 1 if dc > 0 else -1

        r, c = sr + step_r, sc + step_c
        while r != er and c != ec:
            if board[r][c] != " ":
                board[r][c] = " "
                was_capture = True
                captured_positions.append((r, c))
            r += step_r
            c += step_c

    else:
        # ======== REGULAR CHECKER =========
        if abs(dr) == 2 and abs(dc) == 2:
            mid_r = sr + dr // 2
            mid_c = sc + dc // 2
            board[mid_r][mid_c] = " "
            was_capture = True
            captured_positions.append((mid_r, mid_c))

    # ======== MOVEMENT =========
    board[er][ec] = piece
    board[sr][sc] = " "

    if piece == "w" and er == 0:
        board[er][ec] = "W"
    elif piece == "b" and er == 7:
        board[er][ec] = "B"

    return was_capture

def has_more_captures(player_color, r, c):
    piece = board[r][c]

    # ======== QUEEN =========
    if piece.isupper():
        for dr, dc in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
            r2, c2 = r + dr, c + dc
            enemy_found = False

            while 0 <= r2 < 8 and 0 <= c2 < 8:
                if board[r2][c2] == " ":
                    if enemy_found:
                        return True  # можно перепрыгнуть врага
                elif board[r2][c2].lower() == player_color:
                    break  # своя фигура — нельзя
                elif not enemy_found:
                    enemy_found = True  # найден враг
                else:
                    break  # два врага подряд — нельзя
                r2 += dr
                c2 += dc
        return False

    # ======== REGULAR CHECKER =========
    else:
        for dr, dc in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            er, ec = r + dr, c + dc
            mid_r, mid_c = r + dr // 2, c + dc // 2
            if 0 <= er < 8 and 0 <= ec < 8 and 0 <= mid_r < 8 and 0 <= mid_c < 8:
                if board[er][ec] == " ":
                    mid_piece = board[mid_r][mid_c]
                    if mid_piece != " " and mid_piece.lower() != player_color:
                        return True
        return False


def broadcast(msg):
    for c in clients:
        try:
            c.send(msg.encode())
        except:
            pass

def handle_client(conn, addr):
    global clients, players, game_started, current_turn, last_capture_pos
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
        last_capture_pos = None
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

            print(f"=== ПЕРЕД ХОДОМ ===")
            print(f"last_capture_pos: {last_capture_pos}")
            print(f"Ход игрока {players[conn]}: {data}")
            print(f"Координаты: ({sr},{sc}) -> ({er},{ec})")

            if is_valid_move(players[conn], sr, sc, er, ec):
                was_capture = make_move(sr, sc, er, ec)
                broadcast(print_board())

                if was_capture:
                    if has_more_captures(players[conn], er, ec):
                        last_capture_pos = (er, ec)
                        conn.send("Вы можете сделать ещё один ход для продолжения взятия!\n".encode())
                        print(f"Устанавливаем last_capture_pos = {last_capture_pos}")
                        print(f"Можно продолжать бить с позиции ({er},{ec})")
                    else:
                        last_capture_pos = None
                        current_turn = "b" if current_turn == "w" else "w"
                        broadcast(f"Сейчас ход: {current_turn}\n")
                        print(f"Завершение хода, передаем очередь: {current_turn}")
                else:
                    last_capture_pos = None
                    current_turn = "b" if current_turn == "w" else "w"
                    broadcast(f"Сейчас ход: {current_turn}\n")
                    print(f"Обычный ход, передаем очередь: {current_turn}")
            else:
                conn.send("Недопустимый ход\n".encode())

        except Exception as e:
            print(f"Ошибка с игроком {addr}: {e}")
            break

    conn.close()
    if conn in clients:
        clients.remove(conn)
    if conn in players:
        del players[conn]
    print(f"Игрок отключился: {addr}")

def main():
    global last_capture_pos
    last_capture_pos = None
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

