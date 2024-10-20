import socket
import threading

clients = {}
usernames = []

"""
    Send message to all clients except the sender
"""
def broadcast_message(message, sender=None):
    print(f"{message}")
    for client in clients:
        if client != sender:
            try:
                client.send(message.encode('utf-8'))
            except:
                remove_client(client)

"""
    Start a thread for each registered client and handle his actions
"""
def handle_client(client_socket):
    valid_name = False

    while not valid_name:
        username = client_socket.recv(1024).decode('utf-8')
        if len(username) > 10:
            client_socket.send("Username cannot be longer than 10 characters".encode('utf-8'))
        elif username in usernames:
            client_socket.send("Username already taken.".encode('utf-8'))
        else:
            valid_name = True

    client_socket.send(f"Welcome {username}".encode('utf-8'))
    usernames.append(username)
    clients[client_socket] = username
    broadcast_message(f"{username} has joined the chat", client_socket)

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            if message.startswith('@'):
                try:
                    recipient, private_msg = message[1:].split(' ', 1)
                    for client, uname in clients.items():
                        if uname == recipient:
                            client.send(f"[Private] {username}: {private_msg}".encode('utf-8'))
                            break
                except:
                    break
            else:
                broadcast_message(f"{username}: {message}", client_socket)
        except:
            break

    remove_client(client_socket)

"""
    Unregister client
"""
def remove_client(client_socket):
    if client_socket in clients:
        username = clients[client_socket]
        usernames.remove(username)
        del clients[client_socket]
        broadcast_message(f"{username} has left the chat")
        client_socket.close()

"""
    Server startup
"""
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 455))
    server_socket.listen()

    while True:
        client_socket, _ = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

"""
    Server entry point
"""
if __name__ == "__main__":
    start_server()