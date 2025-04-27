# CyberNet-Labs-P2P-File-Sharing-System-decentralized-

# CyberNetLabs-P2P-FileShare

**Decentralized Peer-to-Peer File Sharing System**  
**Developed by CyberNet Labs**

---

## Overview

CyberNet Labs P2P File Share enables direct file sharing between devices with no central server.  
Peer nodes discover each other automatically and share files securely over TCP.

---

## Features

- Decentralized peer discovery (UDP broadcast)
- Distributed Hash Table (DHT) for tracking shared files
- Secure file transfer over TCP
- Works across LAN or VPN (basic NAT traversal)
- Fully cross-platform (Windows, Mac, Linux, Android)

---

## How To Use

1. **Install Python 3.7+**

2. **Clone the repository:**

```bash
git clone https://github.com/your-username/CyberNetLabs-P2P-FileShare.git
cd CyberNetLabs-P2P-FileShare
```
3. **Run the node:**
```bash
python p2p_node.py
```
or 
```bash
python cnl-gui-p2p.py
```


4. **4.	Menu Options:**

	•	View known peers
	•	View available files
	•	Request a file
	•	Exit the node

5.	**Shared Files Location:**

	•	All your shared or downloaded files will be in the shared/ folder.


## License

Licensed under the MIT License
Developed by CyberNet Labs.

