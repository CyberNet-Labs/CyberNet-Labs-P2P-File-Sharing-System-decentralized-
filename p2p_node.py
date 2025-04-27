#!/usr/bin/env python3
"""
CyberNet Labs - Decentralized P2P File Sharing System
Version 1.0
Developed by CyberNet Labs
"""

import socket
import threading
import os
import time
import random

# ======================
# CyberNet Labs Constants
# ======================

BROADCAST_PORT = 50000
TCP_PORT = 50010
BUFFER_SIZE = 4096
PEERS = set()
DHT = {}  # Distributed Hash Table { 'filename': 'peer_ip' }
SHARED_FOLDER = 'shared'

# ======================
# Helper Functions
# ======================

def cybernet_banner():
    print("""
  ____           _              _   _         _       _     
 / ___| ___ _ __| |_ ___ _ __  | \ | | ___   | | __ _| |_   
| |    / _ \ '__| __/ _ \ '__| |  \| |/ _ \  | |/ _` | __|  
| |___|  __/ |  | ||  __/ |    | |\  |  __/  | | (_| | |_   
 \____|\___|_|   \__\___|_|    |_| \_|\___|   |_|\__,_|\__|  

CyberNet Labs - Decentralized P2P File Sharing
------------------------------------------------
""")


def discover_peers():
    """Broadcast presence to other peers."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    message = "CNL_DISCOVERY"
    while True:
        udp_sock.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
        time.sleep(5)  # Broadcast every 5 seconds


def listen_for_peers():
    """Listen for peer discovery messages."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('', BROADCAST_PORT))

    while True:
        data, addr = udp_sock.recvfrom(1024)
        if data.decode() == "CNL_DISCOVERY":
            if addr[0] not in PEERS:
                PEERS.add(addr[0])
                print(f"[+] New peer discovered: {addr[0]}")


def tcp_server():
    """TCP server to accept incoming file requests."""
    tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_sock.bind(('', TCP_PORT))
    tcp_sock.listen(5)
    print("[*] CyberNet Labs TCP Server listening for file requests...")

    while True:
        client_sock, addr = tcp_sock.accept()
        threading.Thread(target=handle_client, args=(client_sock, addr)).start()


def handle_client(client_sock, addr):
    """Serve requested files to peers."""
    try:
        filename = client_sock.recv(BUFFER_SIZE).decode()
        filepath = os.path.join(SHARED_FOLDER, filename)
        
        if os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                while True:
                    bytes_read = f.read(BUFFER_SIZE)
                    if not bytes_read:
                        break
                    client_sock.sendall(bytes_read)
            print(f"[+] Sent file '{filename}' to {addr[0]}")
        else:
            client_sock.send(b"ERROR: File not found")
    except Exception as e:
        print(f"[!] Error handling client: {e}")
    finally:
        client_sock.close()


def update_dht():
    """Update DHT with files this peer has."""
    global DHT
    files = os.listdir(SHARED_FOLDER)
    for file in files:
        if file not in DHT:
            DHT[file] = socket.gethostbyname(socket.gethostname())


def request_file(filename):
    """Request a file from known peers."""
    if filename not in DHT:
        print("[!] File not found in DHT.")
        return

    peer_ip = DHT[filename]
    try:
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((peer_ip, TCP_PORT))
        tcp_sock.sendall(filename.encode())

        save_path = os.path.join(SHARED_FOLDER, f"downloaded-{filename}")
        with open(save_path, 'wb') as f:
            while True:
                data = tcp_sock.recv(BUFFER_SIZE)
                if not data:
                    break
                if data.startswith(b"ERROR"):
                    print(data.decode())
                    os.remove(save_path)
                    return
                f.write(data)

        print(f"[+] File '{filename}' downloaded successfully to {save_path}")

    except Exception as e:
        print(f"[!] Error requesting file: {e}")
    finally:
        tcp_sock.close()

def menu():
    """Display CLI options."""
    while True:
        print("\n--- CyberNet Labs P2P Menu ---")
        print("1. Show known peers")
        print("2. Show available files (DHT)")
        print("3. Request a file")
        print("4. Exit")
        choice = input("Select option: ")

        if choice == '1':
            print("\nKnown Peers:")
            for peer in PEERS:
                print(f" - {peer}")
        elif choice == '2':
            print("\nAvailable Files:")
            for file, owner in DHT.items():
                print(f" - {file} (From {owner})")
        elif choice == '3':
            filename = input("Enter filename to request: ")
            request_file(filename)
        elif choice == '4':
            print("[*] Exiting CyberNet Labs P2P Node...")
            os._exit(0)
        else:
            print("[!] Invalid option.")

def ensure_shared_folder():
    """Create shared folder if not exist."""
    if not os.path.exists(SHARED_FOLDER):
        os.makedirs(SHARED_FOLDER)

def main():
    cybernet_banner()
    ensure_shared_folder()
    update_dht()

    threading.Thread(target=discover_peers, daemon=True).start()
    threading.Thread(target=listen_for_peers, daemon=True).start()
    threading.Thread(target=tcp_server, daemon=True).start()

    menu()

if __name__ == "__main__":
    main()
