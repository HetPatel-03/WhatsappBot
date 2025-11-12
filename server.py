"""
WhatsApp-like Chat Server with Clock Synchronization
Implements multi-client chat server with Cristian's clock synchronization algorithm
"""

import socket
import threading
import time
import json
from datetime import datetime

class ChatServer:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []  # List of client connections
        self.clients_lock = threading.Lock()  # Lock for thread-safe client list access
        self.server_clock = time.time()  # Server's clock (Unix timestamp)
        self.clock_lock = threading.Lock()  # Lock for thread-safe clock access
        
    def get_server_time(self):
        """Get current server time"""
        with self.clock_lock:
            return self.server_clock
    
    def update_server_clock(self):
        """Update server clock (simulates real-time progression)"""
        with self.clock_lock:
            self.server_clock = time.time()
    
    def handle_client(self, client_socket, client_address):
        """
        Handle individual client connection
        Uses threading to handle multiple clients concurrently
        """
        print(f"[NEW CONNECTION] {client_address} connected.")
        
        try:
            while True:
                # Receive message from client
                message = client_socket.recv(1024).decode('utf-8')
                
                if not message:
                    break
                
                try:
                    data = json.loads(message)
                    message_type = data.get('type')
                    
                    if message_type == 'sync_request':
                        # Handle clock synchronization request (Cristian's algorithm)
                        self.handle_sync_request(client_socket, data)
                    
                    elif message_type == 'chat_message':
                        # Handle chat message - broadcast to all clients
                        self.broadcast_message(data, client_address)
                    
                    else:
                        print(f"[UNKNOWN] Unknown message type from {client_address}")
                        
                except json.JSONDecodeError:
                    print(f"[ERROR] Invalid JSON from {client_address}: {message}")
                    
        except ConnectionResetError:
            print(f"[DISCONNECT] {client_address} disconnected unexpectedly")
        except Exception as e:
            print(f"[ERROR] Error handling client {client_address}: {e}")
        finally:
            # Remove client from list and close connection
            with self.clients_lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)
            client_socket.close()
            print(f"[DISCONNECT] {client_address} disconnected. Active clients: {len(self.clients)}")
    
    def handle_sync_request(self, client_socket, data):
        """
        Implement Cristian's clock synchronization algorithm
        
        Cristian's Algorithm:
        1. Client sends sync request with T0 (client's time when request sent)
        2. Server receives request at T1 (server's time)
        3. Server responds with T1 and T2 (server's time when response sent)
        4. Client receives response at T3 (client's time)
        5. Client calculates: offset = ((T1 + T2) / 2) - T0
        6. Client adjusts clock: new_time = T3 + offset
        """
        self.update_server_clock()
        T1 = self.get_server_time()  # Server time when request received
        
        # Create response with server time
        response = {
            'type': 'sync_response',
            'T1': T1,  # Server time when request received
            'T0': data.get('T0', 0)  # Echo back client's T0 for verification
        }
        
        # Small delay to simulate processing
        time.sleep(0.001)
        
        self.update_server_clock()
        T2 = self.get_server_time()  # Server time when response sent
        response['T2'] = T2
        
        # Send response to client
        try:
            client_socket.send(json.dumps(response).encode('utf-8'))
            print(f"[SYNC] Clock sync response sent to client")
        except Exception as e:
            print(f"[ERROR] Failed to send sync response: {e}")
    
    def broadcast_message(self, message_data, sender_address):
        """
        Broadcast message to all connected clients except the sender
        Thread-safe broadcasting using locks
        """
        # Add server timestamp to message
        self.update_server_clock()
        message_data['server_timestamp'] = self.get_server_time()
        message_data['sender_address'] = str(sender_address)
        
        message_json = json.dumps(message_data)
        disconnected_clients = []
        
        # Thread-safe access to clients list
        with self.clients_lock:
            clients_to_notify = self.clients.copy()
        
        # Broadcast to all clients
        for client in clients_to_notify:
            try:
                client.send(message_json.encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to send message to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        if disconnected_clients:
            with self.clients_lock:
                for client in disconnected_clients:
                    if client in self.clients:
                        self.clients.remove(client)
        
        # Print message to server console
        username = message_data.get('username', 'Unknown')
        message = message_data.get('message', '')
        print(f"[MESSAGE] {username} ({sender_address}): {message}")
    
    def start(self):
        """Start the chat server"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[SERVER] Server started on {self.host}:{self.port}")
            print(f"[SERVER] Waiting for clients...")
            
            while True:
                # Accept new client connection
                client_socket, client_address = self.server_socket.accept()
                
                # Add client to list (thread-safe)
                with self.clients_lock:
                    self.clients.append(client_socket)
                
                # Create thread for each client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                )
                client_thread.start()
                print(f"[ACTIVE CONNECTIONS] {len(self.clients)}")
                
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")
        except Exception as e:
            print(f"[ERROR] Server error: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()
            print("[SERVER] Server closed.")

if __name__ == "__main__":
    server = ChatServer(host='localhost', port=8888)
    server.start()

