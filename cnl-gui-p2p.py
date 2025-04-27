#!/usr/bin/env python3
"""
CyberNet Labs - P2P File Sharing System (Luxurious GUI)
Version 1.1
Developed by CyberNet Labs
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import socket
import os
import time

# === CyberNet Labs Constants ===
BROADCAST_PORT = 50000
TCP_PORT       = 50010
BUFFER_SIZE    = 4096
PEERS          = set()
DHT            = {}
SHARED_FOLDER  = 'shared'

# === Ensure shared folder exists ===
os.makedirs(SHARED_FOLDER, exist_ok=True)

# === Networking logic ===

def discover_peers():
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        udp.sendto(b"CNL_DISCOVERY", ('<broadcast>', BROADCAST_PORT))
        time.sleep(5)

def listen_for_peers(callback):
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(('', BROADCAST_PORT))
    while True:
        data, addr = udp.recvfrom(1024)
        if data == b"CNL_DISCOVERY" and addr[0] not in PEERS:
            PEERS.add(addr[0])
            callback()

def tcp_server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(('', TCP_PORT))
    srv.listen(5)
    while True:
        client, addr = srv.accept()
        threading.Thread(target=handle_client, args=(client,), daemon=True).start()

def handle_client(sock):
    try:
        name = sock.recv(BUFFER_SIZE).decode()
        path = os.path.join(SHARED_FOLDER, name)
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                while chunk := f.read(BUFFER_SIZE):
                    sock.sendall(chunk)
        else:
            sock.sendall(b"ERROR: File not found")
    finally:
        sock.close()

def update_dht():
    for fname in os.listdir(SHARED_FOLDER):
        if fname not in DHT:
            DHT[fname] = socket.gethostbyname(socket.gethostname())

def request_file(fname, status_cb):
    if fname not in DHT:
        status_cb("❌ Not in DHT")
        return
    peer = DHT[fname]
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((peer, TCP_PORT))
        s.sendall(fname.encode())
        out = os.path.join(SHARED_FOLDER, f"dl-{fname}")
        with open(out, 'wb') as f:
            while chunk := s.recv(BUFFER_SIZE):
                if chunk.startswith(b"ERROR"):
                    status_cb(chunk.decode())
                    os.remove(out)
                    return
                f.write(chunk)
        status_cb(f"✅ Saved to {out}")
        update_dht()
    except Exception as e:
        status_cb(f"❌ {e}")
    finally:
        s.close()

# === GUI ===

class LuxGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CyberNet Labs P2P Share")
        self.geometry("650x540")
        self.configure(bg="#ECECEC")
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self._create_styles()
        self._build_ui()
        update_dht()
        threading.Thread(target=discover_peers, daemon=True).start()
        threading.Thread(target=listen_for_peers, args=(self._refresh_peers,), daemon=True).start()
        threading.Thread(target=tcp_server, daemon=True).start()

    def _create_styles(self):
        s = self.style
        s.configure("Header.TLabel", background="#ECECEC",
                    font=("Helvetica Neue", 22, "bold"),
                    foreground="#111")
        s.configure("Panel.TFrame", background="white", relief="flat")
        s.configure("TLabel", background="white",
                    font=("Helvetica Neue", 12),
                    foreground="#333")
        s.configure("TEntry", font=("Helvetica Neue", 12))
        s.configure("Accent.TButton",
                    background="#007AFF", foreground="white",
                    font=("Helvetica Neue", 13), padding=8)
        s.map("Accent.TButton",
              background=[("active", "#005BBB")])

    def _build_ui(self):
        # Header
        ttk.Label(self, text="CyberNet Labs P2P Share", style="Header.TLabel").pack(pady=(20,10))

        # Status
        self.status = ttk.Label(self, text="Status: Idle", anchor="center")
        self.status.pack(fill='x', padx=50, pady=(0,20))

        # Panels container
        pan = ttk.Frame(self, style="Panel.TFrame")
        pan.pack(fill='both', expand=True, padx=30, pady=10)

        # Peers panel
        peer_frame = ttk.LabelFrame(pan, text="Known Peers", style="Panel.TFrame")
        peer_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.peers_lb = tk.Listbox(peer_frame, height=6, bd=0, font=("Helvetica Neue", 12))
        self.peers_lb.pack(fill='both', expand=True, padx=5, pady=5)

        # Files panel
        file_frame = ttk.LabelFrame(pan, text="Available Files", style="Panel.TFrame")
        file_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.files_lb = tk.Listbox(file_frame, height=6, bd=0, font=("Helvetica Neue", 12))
        self.files_lb.pack(fill='both', expand=True, padx=5, pady=5)

        pan.columnconfigure(0, weight=1)
        pan.columnconfigure(1, weight=1)

        # Request area
        req = ttk.Frame(self, style="Panel.TFrame")
        req.pack(fill='x', padx=30, pady=(0,20))
        self.entry = ttk.Entry(req)
        self.entry.pack(side='left', fill='x', expand=True, padx=(5,10))
        btn = ttk.Button(req, text="Download", style="Accent.TButton", command=self._on_download)
        btn.pack(side='right')

        # Initial population
        self._refresh_peers()
        self._refresh_files()

    def _refresh_peers(self):
        self.peers_lb.delete(0, tk.END)
        for p in sorted(PEERS):
            self.peers_lb.insert(tk.END, p)

    def _refresh_files(self):
        self.files_lb.delete(0, tk.END)
        update_dht()
        for f in sorted(DHT):
            self.files_lb.insert(tk.END, f)

    def _on_download(self):
        fname = self.entry.get().strip()
        if not fname:
            messagebox.showwarning("Enter Name", "Please type a filename first.")
            return
        self.status.config(text="Status: Downloading…")
        threading.Thread(target=request_file, args=(fname, self._update_status), daemon=True).start()

    def _update_status(self, msg):
        self.status.config(text=f"Status: {msg}")
        self._refresh_files()

if __name__ == "__main__":
    LuxGUI().mainloop()
