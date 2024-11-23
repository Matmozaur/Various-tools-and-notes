import socket

HOST = '127.0.0.1'  # Server address
PORT = 65432        # Same port as the server

def run_client():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((HOST, PORT))
        message = "Hello, Server!"
        print(f"Sending: {message}")
        sock.sendall(message.encode())
        data = sock.recv(1024)
        print(f"Received from server: {data.decode()}")

if __name__ == "__main__":
    run_client()
