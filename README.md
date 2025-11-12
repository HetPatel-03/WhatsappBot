# WhatsappBot

This project implements a multi-client chat application similar to WhatsApp, featuring real-time message broadcasting and clock synchronization using Cristian's algorithm. The system consists of a central server that manages multiple client connections and a client application with a graphical user interface built using Tkinter.

## Quick Start

### 1. Start the Server
```bash
python server.py
```
The server will start on `localhost:8888` and wait for client connections.

### 2. Start Client(s)
Open one or more terminal windows and run:
```bash
python client.py
```

### 3. Connect and Chat
1. Enter a username in the client GUI
2. Click "Connect" to join the chat
3. Type messages and press Enter or click "Send"
4. Messages will be broadcast to all connected clients
5. Clock synchronization happens automatically every 5 seconds

## Features

- ✅ Multi-client chat communication
- ✅ Real-time message broadcasting
- ✅ Clock synchronization using Cristian's algorithm
- ✅ Threading for concurrent client handling
- ✅ Tkinter GUI with time displays
- ✅ Message timestamps (client and server time)

## Files

- `server.py` - Chat server implementation
- `client.py` - Chat client with GUI
- `Technical_Report.md` - Technical documentation

## Requirements

- Python 3.x
- tkinter (usually included with Python)
- No external dependencies required
