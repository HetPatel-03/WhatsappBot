"""
WhatsApp-like Chat Client with Clock Synchronization
Implements client with Tkinter GUI and Cristian's clock synchronization
"""

import socket
import threading
import time
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import random

class ChatClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.username = None
        self.connected = False
        
        # Clock synchronization variables
        self.local_clock = time.time()  # Client's local clock
        self.synced_clock = time.time()  # Synchronized clock (server time)
        self.clock_offset = 0.0  # Offset from server time
        self.clock_drift_rate = 0.0  # Simulated drift rate (optional)
        
        # GUI components
        self.root = None
        self.chat_display = None
        self.message_entry = None
        self.local_time_label = None
        self.synced_time_label = None
        self.username_entry = None
        
        # Threading
        self.receive_thread = None
        self.sync_thread = None
        self.sync_response_queue = []  # Queue for sync responses
        self.sync_lock = threading.Lock()  # Lock for sync coordination
        
    def get_local_time(self):
        """Get current local time (with optional drift simulation)"""
        # Simulate clock drift by adding small random offset
        drift = random.uniform(-0.01, 0.01) * self.clock_drift_rate
        return time.time() + drift
    
    def update_synced_clock(self):
        """Update synchronized clock based on offset"""
        self.synced_clock = self.get_local_time() + self.clock_offset
    
    def synchronize_clock(self):
        """
        Implement Cristian's clock synchronization algorithm
        
        Steps:
        1. Send sync request with T0 (local time when request sent)
        2. Receive response with T1 (server time when request received) and T2 (server time when response sent)
        3. Record T3 (local time when response received)
        4. Calculate offset: offset = ((T1 + T2) / 2) - T0
        5. Adjust clock: synced_time = T3 + offset
        """
        if not self.connected:
            return False
        
        try:
            # Step 1: Send sync request with T0
            T0 = self.get_local_time()
            sync_request = {
                'type': 'sync_request',
                'T0': T0
            }
            
            # Clear any old sync responses
            with self.sync_lock:
                self.sync_response_queue.clear()
            
            # Send sync request
            self.socket.send(json.dumps(sync_request).encode('utf-8'))
            
            # Step 2: Wait for response (handled by receive thread)
            # Wait up to 2 seconds for sync response
            timeout = 2.0
            start_wait = time.time()
            response_data = None
            
            while time.time() - start_wait < timeout:
                with self.sync_lock:
                    if self.sync_response_queue:
                        response_data = self.sync_response_queue.pop(0)
                        break
                time.sleep(0.01)  # Small sleep to avoid busy waiting
            
            if response_data is None:
                print(f"[SYNC] Timeout waiting for sync response")
                return False
            
            # Step 3: Record T3 when we process the response
            T3 = self.get_local_time()
            
            T1 = response_data.get('T1', 0)
            T2 = response_data.get('T2', 0)
            
            # Step 4: Calculate offset using Cristian's algorithm
            # Round-trip time: RTT = (T3 - T0)
            # Server time estimate: server_time = (T1 + T2) / 2
            # Offset: difference between server time and client time
            server_time_estimate = (T1 + T2) / 2
            self.clock_offset = server_time_estimate - T0
            
            # Step 5: Update synchronized clock
            self.synced_clock = T3 + self.clock_offset
            
            print(f"[SYNC] Clock synchronized. Offset: {self.clock_offset:.4f}s")
            return True
                
        except Exception as e:
            print(f"[ERROR] Clock synchronization failed: {e}")
            return False
    
    def connect_to_server(self):
        """Connect to the chat server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Perform initial clock synchronization
            self.synchronize_clock()
            
            # Start receiving thread
            self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
            self.receive_thread.start()
            
            # Start periodic clock synchronization thread
            self.sync_thread = threading.Thread(target=self.periodic_sync, daemon=True)
            self.sync_thread.start()
            
            return True
            
        except Exception as e:
            messagebox.showerror("Connection Error", f"Failed to connect to server: {e}")
            return False
    
    def receive_messages(self):
        """Receive messages from server in a separate thread"""
        while self.connected:
            try:
                message = self.socket.recv(1024).decode('utf-8')
                if not message:
                    break
                
                data = json.loads(message)
                
                if data.get('type') == 'chat_message':
                    # Only display if it's not our own message (to avoid duplicates)
                    # We already displayed it locally when sending
                    if data.get('username') != self.username:
                        # Display received message in GUI
                        self.root.after(0, self.display_message, data)
                elif data.get('type') == 'sync_response':
                    # Handle sync response - add to queue for sync thread
                    with self.sync_lock:
                        self.sync_response_queue.append(data)
                    
            except json.JSONDecodeError:
                print(f"[ERROR] Invalid JSON received: {message}")
            except Exception as e:
                if self.connected:
                    print(f"[ERROR] Error receiving message: {e}")
                break
        
        self.connected = False
        self.root.after(0, lambda: messagebox.showwarning("Disconnected", "Connection to server lost."))
    
    def periodic_sync(self):
        """Periodically synchronize clock with server (every 5 seconds)"""
        while self.connected:
            time.sleep(5)  # Sync every 5 seconds
            if self.connected:
                self.synchronize_clock()
    
    def send_message(self, message_text):
        """Send chat message to server"""
        if not self.connected or not message_text.strip():
            return
        
        try:
            # Get local time for timestamp
            local_timestamp = self.get_local_time()
            
            message_data = {
                'type': 'chat_message',
                'username': self.username,
                'message': message_text,
                'client_timestamp': local_timestamp
            }
            
            # Display message locally immediately (before server broadcast)
            self.display_message(message_data)
            
            # Send to server
            self.socket.send(json.dumps(message_data).encode('utf-8'))
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send message: {e}")
    
    def display_message(self, message_data):
        """Display message in chat window"""
        username = message_data.get('username', 'Unknown')
        message = message_data.get('message', '')
        client_timestamp = message_data.get('client_timestamp', 0)
        server_timestamp = message_data.get('server_timestamp', 0)
        
        # Format timestamps
        if client_timestamp:
            client_time_str = datetime.fromtimestamp(client_timestamp).strftime('%H:%M:%S')
        else:
            client_time_str = "N/A"
        
        if server_timestamp:
            server_time_str = datetime.fromtimestamp(server_timestamp).strftime('%H:%M:%S')
        else:
            server_time_str = "N/A"
        
        # Format message display
        display_text = f"[{client_time_str}] {username}: {message}\n"
        
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, display_text)
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)
    
    def update_time_displays(self):
        """Update time display labels"""
        if not self.connected:
            return
        
        # Update synchronized clock
        self.update_synced_clock()
        
        # Format and display local time
        local_time = datetime.fromtimestamp(self.get_local_time())
        local_time_str = local_time.strftime('%H:%M:%S.%f')[:-3]
        self.local_time_label.config(text=f"Local Time: {local_time_str}")
        
        # Format and display synchronized time
        synced_time = datetime.fromtimestamp(self.synced_clock)
        synced_time_str = synced_time.strftime('%H:%M:%S.%f')[:-3]
        offset_str = f"{self.clock_offset:+.4f}s" if self.clock_offset != 0 else "0.0000s"
        self.synced_time_label.config(text=f"Synced Time: {synced_time_str} (Offset: {offset_str})")
        
        # Schedule next update
        self.root.after(100, self.update_time_displays)  # Update every 100ms
    
    def on_send_click(self):
        """Handle send button click"""
        message = self.message_entry.get()
        if message.strip():
            self.send_message(message)
            self.message_entry.delete(0, tk.END)
    
    def on_enter_press(self, event):
        """Handle Enter key press in message entry"""
        self.on_send_click()
    
    def create_gui(self):
        """Create Tkinter GUI for chat application"""
        self.root = tk.Tk()
        self.root.title("WhatsApp-like Chat Client")
        self.root.geometry("700x600")
        
        # Username frame
        username_frame = tk.Frame(self.root)
        username_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(username_frame, text="Username:", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.username_entry = tk.Entry(username_frame, font=("Arial", 10), width=20)
        self.username_entry.pack(side=tk.LEFT, padx=5)
        self.username_entry.insert(0, f"User_{random.randint(1000, 9999)}")
        
        connect_button = tk.Button(username_frame, text="Connect", command=self.on_connect_click, 
                                   bg="#25D366", fg="white", font=("Arial", 10, "bold"))
        connect_button.pack(side=tk.LEFT, padx=10)
        
        # Time display frame
        time_frame = tk.Frame(self.root, bg="#ECE5DD")
        time_frame.pack(pady=5, padx=10, fill=tk.X)
        
        self.local_time_label = tk.Label(time_frame, text="Local Time: --:--:--", 
                                        font=("Arial", 9), bg="#ECE5DD")
        self.local_time_label.pack(side=tk.LEFT, padx=10)
        
        self.synced_time_label = tk.Label(time_frame, text="Synced Time: --:--:-- (Offset: 0.0000s)", 
                                         font=("Arial", 9), bg="#ECE5DD")
        self.synced_time_label.pack(side=tk.LEFT, padx=10)
        
        # Chat display area
        chat_frame = tk.Frame(self.root)
        chat_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                      font=("Arial", 10), state=tk.DISABLED,
                                                      bg="#ECE5DD", fg="#000000")
        self.chat_display.pack(fill=tk.BOTH, expand=True)
        
        # Message input frame
        input_frame = tk.Frame(self.root)
        input_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.message_entry = tk.Entry(input_frame, font=("Arial", 11))
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.message_entry.bind("<Return>", self.on_enter_press)
        
        send_button = tk.Button(input_frame, text="Send", command=self.on_send_click,
                               bg="#25D366", fg="white", font=("Arial", 11, "bold"),
                               width=10)
        send_button.pack(side=tk.RIGHT, padx=5)
        
        # Welcome message
        self.chat_display.config(state=tk.NORMAL)
        self.chat_display.insert(tk.END, "Welcome! Enter your username and click Connect to join the chat.\n\n")
        self.chat_display.config(state=tk.DISABLED)
    
    def on_connect_click(self):
        """Handle connect button click"""
        if self.connected:
            messagebox.showinfo("Info", "Already connected to server.")
            return
        
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter a username.")
            return
        
        self.username = username
        self.username_entry.config(state=tk.DISABLED)
        
        if self.connect_to_server():
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"Connected to server as {username}!\n")
            self.chat_display.config(state=tk.DISABLED)
            self.update_time_displays()  # Start time updates
        else:
            self.username_entry.config(state=tk.NORMAL)
    
    def run(self):
        """Run the client application"""
        self.create_gui()
        self.root.mainloop()
        
        # Cleanup on close
        self.connected = False
        if self.socket:
            self.socket.close()

if __name__ == "__main__":
    # Optional: Enable clock drift simulation
    # Set clock_drift_rate to a non-zero value to simulate drift
    client = ChatClient(host='localhost', port=8888)
    client.clock_drift_rate = 0.0  # Set to 1.0 or higher to enable drift simulation
    client.run()

