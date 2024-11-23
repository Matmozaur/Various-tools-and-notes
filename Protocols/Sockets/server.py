import socket
import selectors

HOST = '127.0.0.1'  # Localhost
PORT = 65432  # Arbitrary non-privileged port

sel = selectors.DefaultSelector()


def accept(sock):
    conn, addr = sock.accept()  # Accept the new connection
    print(f"Connected by {addr}")
    conn.setblocking(False)  # Set non-blocking mode
    sel.register(conn, selectors.EVENT_READ, handle_client)


def handle_client(conn):
    try:
        data = conn.recv(1024)  # Read data
        if data:
            print(f"Received: {data.decode()}")
            conn.sendall(data)  # Echo the data back
        else:
            sel.unregister(conn)
            conn.close()
    except ConnectionResetError:
        sel.unregister(conn)
        conn.close()


if __name__ == '__main__':
    # Setup server socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        server_sock.bind((HOST, PORT))
        server_sock.listen()
        server_sock.setblocking(False)
        sel.register(server_sock, selectors.EVENT_READ, accept)
        print(f"Server listening on {HOST}:{PORT}")

        while True:
            events = sel.select()  # Wait for events
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)
