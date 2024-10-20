import socket
import threading
import sys
import os

"""
    Handle incoming messages
"""
def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break
            else:
                if "[FILE]" in message:
                    handle_file_transfer(client_socket, message)
                else:
                    sys.stdout.write(f"\r{message}\n")
                    sys.stdout.flush()
        except Exception as e:
            print(f"[ERROR] {e}")
            break

"""
    Receive file from other client
"""
def handle_file_transfer(client_socket, message):
    _, _, _, filename, filesize_str = message.split(" ")
    filesize = int(filesize_str) -1
    received_bytes = 0
    new_file = "received_" + filename
    with open(new_file, 'wb') as f:
        print(f"Receiving file: {filename} ({filesize} bytes)")

        while received_bytes < filesize:
            chunk = client_socket.recv(1024).decode('utf-8')

            if not chunk:
                print("Connection closed unexpectedly.")
                break

            chunk_data = chunk.split("[CHUNK]")[-1].strip()
            f.write(chunk_data.encode('utf-8'))

            received_bytes += len(chunk_data.encode('utf-8'))
            print(f"Received {len(chunk_data.encode('utf-8'))} bytes, total received: {received_bytes}/{filesize} bytes")
        f.write(b'\n')

    if received_bytes == filesize:
        print("File transfer complete.")
    else:
        print("File transfer incomplete. Expected:", filesize, "bytes, but received:", received_bytes, "bytes.")


"""
    Send messages to other clients
"""
def send_messages(client_socket):
    while True:
        mode = input("")
        if mode.startswith('@'):
            recipient, message = mode[1:].split(' ', 1)
            if message.startswith("/sendfile "):
                _, message = message.split(" ", 1)
                send_file(client_socket, recipient, message)
            else:
                client_socket.send(f"@{recipient} {message}".encode('utf-8'))
        else:
            client_socket.send(mode.encode('utf-8'))

"""
    File sending
"""
def send_file(client_socket, recipient, file):
    if not is_file_valid(file):
        return

    filesize = os.path.getsize(file)
    filename = os.path.basename(file)
    initiate_file_transmission(client_socket, recipient, filename, filesize)
    sent_bytes = 0

    recipient_prefix = f"@{recipient} [CHUNK] "
    prefix_length = len(recipient_prefix)

    with open(file, 'rb') as f:
        while sent_bytes < filesize:
            filedata = f.read(1024-prefix_length)
            
            print(f"sending {len(filedata)}")

            message = (recipient_prefix + filedata.decode('latin1')).encode('utf-8')
            client_socket.sendall(message)

            sent_bytes += len(filedata)
        f.close()
    
    print("[INFO] file transfer complete.")

"""
    Check if file exists and client has read permission
"""
def is_file_valid(file):
    if not os.path.isfile(file):
        print(f"[ERROR] {file} not found")
        return False
    if not os.access(file, os.R_OK):
        print(f"[ERROR] no read permission for {file}")
        return False
    return True

"""
   Initiate a file sharing session with another client
"""
def initiate_file_transmission(client_socket, recipient, filename, filesize):
    client_socket.send(f"@{recipient} [FILE] {filename} {filesize}".encode('utf-8'))

"""
    Client initiation
"""
def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 455))

    username = input("Enter username: ")
    client_socket.send(username.encode('utf-8'))

    while True:
        response = client_socket.recv(1024).decode('utf-8')
        print(response)
        if response.startswith("Username already taken"):
            username = input("Enter another username: ")
            client_socket.send(username.encode('utf-8'))
        else:
            break

    thread = threading.Thread(target=receive_messages, args=(client_socket,))
    thread.start()

    send_messages(client_socket)

"""
    Client entry point
"""
if __name__ == "__main__":
    start_client()