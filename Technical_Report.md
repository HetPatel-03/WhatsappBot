# Technical Report: WhatsApp-like Chat Application with Clock Synchronization

## Overview
This report documents the implementation of a multi-client chat application with clock synchronization using Python sockets, threading, and Tkinter. The system implements Cristian's algorithm for clock synchronization and supports real-time message broadcasting among multiple clients.

## 1. Server-Client Communication Architecture

### Server Implementation
The server (`server.py`) uses a multi-threaded architecture to handle multiple clients concurrently:

- **Socket Setup**: The server binds to `localhost:8888` and listens for incoming connections
- **Threading Model**: Each client connection is handled by a separate thread (`handle_client` method), allowing the server to process multiple clients simultaneously without blocking
- **Thread Safety**: The `clients` list is protected by a `threading.Lock()` to ensure thread-safe access when adding/removing clients or broadcasting messages

### Client Implementation
The client (`client.py`) maintains a persistent connection to the server:

- **Connection Management**: Establishes a TCP socket connection to the server on startup
- **Dual Threading**: Uses two separate threads:
  - `receive_messages`: Continuously listens for incoming messages from the server
  - `periodic_sync`: Performs clock synchronization every 5 seconds
- **GUI Thread**: The main Tkinter thread handles user interface updates and user input

### Message Protocol
Communication uses JSON-encoded messages with the following structure:

**Sync Request:**
```json
{
  "type": "sync_request",
  "T0": <client_timestamp>
}
```

**Sync Response:**
```json
{
  "type": "sync_response",
  "T1": <server_time_when_received>,
  "T2": <server_time_when_sent>,
  "T0": <echoed_client_T0>
}
```

**Chat Message:**
```json
{
  "type": "chat_message",
  "username": "<username>",
  "message": "<message_text>",
  "client_timestamp": <client_local_time>,
  "server_timestamp": <server_time>
}
```

## 2. Clock Synchronization: Cristian's Algorithm

### Algorithm Implementation
Cristian's algorithm is implemented to synchronize client clocks with the server clock:

**Step 1**: Client sends sync request with `T0` (local time when request is sent)

**Step 2**: Server receives request at `T1` (server's current time)

**Step 3**: Server sends response with `T1` and `T2` (server time when response is sent)

**Step 4**: Client receives response at `T3` (local time when response received)

**Step 5**: Client calculates offset:
```
offset = ((T1 + T2) / 2) - T0
```

**Step 6**: Client adjusts synchronized clock:
```
synced_clock = T3 + offset
```

### Key Features
- **Periodic Synchronization**: Clients automatically synchronize every 5 seconds
- **Offset Calculation**: The offset represents the difference between server time and client time
- **Real-time Display**: The GUI displays both local time and synchronized time with the offset
- **Drift Simulation**: Optional clock drift can be enabled by setting `clock_drift_rate` to simulate clock skew

### Clock Management
- Server maintains its own clock using `time.time()` (Unix timestamp)
- Client maintains both local clock and synchronized clock
- The synchronized clock is continuously updated based on the calculated offset
- Time displays update every 100ms for smooth visualization

## 3. Threading Implementation

### Server Threading
The server uses threading to handle multiple clients:

1. **Main Thread**: Accepts new client connections in a loop
2. **Client Threads**: Each client connection spawns a new daemon thread that:
   - Receives messages from the client
   - Processes sync requests and chat messages
   - Broadcasts messages to all connected clients
   - Handles client disconnection

**Thread Safety Mechanisms:**
- `clients_lock`: Protects the `clients` list during add/remove operations
- `clock_lock`: Protects server clock access during synchronization
- Thread-safe broadcasting ensures messages are sent to all clients without race conditions

### Client Threading
The client uses threading for concurrent operations:

1. **Main Thread (GUI)**: Handles Tkinter interface, user input, and display updates
2. **Receive Thread**: Continuously receives messages from server without blocking GUI
3. **Sync Thread**: Periodically performs clock synchronization

**Thread Communication:**
- GUI updates from background threads use `root.after()` to safely update Tkinter widgets
- Thread-safe message queuing ensures received messages are displayed correctly

### Concurrency Benefits
- **Non-blocking Operations**: Server can handle multiple clients simultaneously
- **Responsive GUI**: Client interface remains responsive while receiving messages
- **Real-time Communication**: Messages are broadcast and received in real-time
- **Scalability**: Server can handle as many clients as system resources allow

## 4. GUI Implementation

### Tkinter Interface Components
- **Chat Display**: ScrolledText widget showing all messages with timestamps
- **Message Input**: Entry field for typing new messages
- **Time Displays**: Labels showing local time and synchronized server time with offset
- **Username Entry**: Field for entering username before connecting
- **Connect Button**: Initiates connection to server

### User Experience Features
- Enter key support for sending messages
- Real-time time display updates (100ms refresh rate)
- Message timestamps showing both client and server times
- Color-coded interface (WhatsApp-inspired green theme)
- Automatic scrolling to latest messages

## 5. Testing and Verification

### Multi-Client Testing
To test the application:

1. Start the server: `python server.py`
2. Launch multiple client instances: `python client.py`
3. Enter different usernames for each client
4. Send messages from different clients
5. Verify:
   - Messages are broadcast to all clients
   - Clock synchronization occurs every 5 seconds
   - Time displays show correct local and synchronized times
   - Multiple clients can send messages concurrently

### Expected Behavior
- All clients receive messages from all other clients
- Clock synchronization happens automatically every 5 seconds
- Time offset is displayed and updated in real-time
- Server console shows connection status and message logs
- Clients can connect/disconnect without affecting other clients

## 6. Code Quality and Structure

### Design Patterns
- **Object-Oriented Design**: Clean class-based structure for server and client
- **Separation of Concerns**: Clear separation between networking, synchronization, and GUI
- **Error Handling**: Comprehensive try-except blocks for robust error handling
- **Resource Management**: Proper socket cleanup on disconnect

### Code Organization
- Well-commented code explaining key algorithms and operations
- Consistent naming conventions
- Modular functions for specific tasks
- Thread-safe implementations with proper locking mechanisms

## Conclusion

This implementation successfully demonstrates:
- Multi-client chat communication using Python sockets
- Clock synchronization using Cristian's algorithm
- Concurrent client handling using threading
- User-friendly GUI with Tkinter
- Real-time message broadcasting
- Robust error handling and thread safety

The system is fully functional and ready for multi-client testing, demonstrating all required features including clock synchronization, threading, and GUI implementation.

