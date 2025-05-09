import threading
from queue import Queue
import json
import Globals

class MessageBroker:
    _instance = None

    def __new__(cls, *args, **kwargs):
        # singleton patter
        if cls._instance is None:
            cls._instance = super(MessageBroker, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'): 
            self.initialized = True
            self.message_queue = Queue()  # Thread-safe queue for storing messages
            self.websockets = set()
            self.sockets = set()
            self.lock = threading.Lock()

    def add_message(self, message):
        """Add a message to the queue."""
        self.message_queue.put(message)

    def add_websocket(self, websocket):
        """Register a new WebSocket client."""
        with self.lock:
            self.websockets.add(websocket)

    def remove_websocket(self, websocket):
        """Remove a WebSocket client."""
        with self.lock:
            self.websockets.discard(websocket)

    def add_socket(self, socket_client):
        """Register a new Socket client."""
        with self.lock:
            self.sockets.add(socket_client)

    def remove_socket(self, socket_client):
        """Remove a Socket client."""
        with self.lock:
            self.sockets.discard(socket_client)

    def broadcast(self):
        """Send messages from the queue to all connected clients."""
        while not self.message_queue.empty():
            message = self.message_queue.get()
            with self.lock:
                # Broadcast to WebSocket clients
                for websocket in list(self.websockets):
                    try:
                        # Incoming message: {"Message": message["Message"], "Number": message["Number"], "Content": message["msg"]}
                        # Need to encode message["msg"] in json so it will be safe
                        smi = message["msg"]
                        smj = json.dumps(smi)
                        smf = { "Message": message["Message"], "Number": message["Number"], "Content": smj}
                        websocket.write_message(json.dumps(smf))  # write_message() implemented by WebSocket class, and part of set().  Intellisense fail
                    except ConnectionError:
                        self.websockets.remove(websocket)
                # Broadcast to Socket clients
                for socket_client in list(self.sockets):
                    try:
                        # loop through key:pair to assemble string message
                        msgString = ""
                        for key in message["msg"]: 
                            if key == "PowerControlName":
                                pass
                            else: 
                                msgString += (key + ":" + bool2string(message["msg"][key]) + ",")
                        # get rid of trailing comma
                        msg = msgString.rstrip(",") + "\n"
                        socket_client.sendall(msg.encode('utf-8')) # send() implemented by Socket class
                    except IOError:
                        self.sockets.remove(socket_client)

    # Does not use message cue
    def ws_post_message(self, message):
        # message is object with reply number and string response
        with self.lock:
            # Broadcast to WebSocket clients
            for websocket in list(self.websockets):
                try:
                    # Incoming message is dictionary. 2001 = Reply Message 2004 = Switch Update Message
                    smj = json.dumps(message["msg"])
                    smf = { "Message": message["Message"], "Number": message["Number"], "Content": smj}
                    websocket.write_message(json.dumps(smf))  # write_message() implemented by WebSocket class, and part of set().  Intellisense fail
                except IOError:
                    self.websockets.remove(websocket)

    # Does not use message cue
    def s_post_message(self, message):
        with self.lock:
            for socket_client in list(self.sockets):
                try: 
                    socket_client.sendall(message.encode('utf-8'))
                except IOError: 
                    self.sockets.remove(socket_client)

def bool2string(bool):
    if bool == True: 
        return "true"
    elif bool == False: 
        return "false"
    else: 
        return "\"" + bool + "\""


    # Get Power Control status: 2001
    # Get interlock status:     2002
    # Change relay state:       2003
    # Get Device Status:        2004
    # Start/Stop command:       2005
    # Switch Status:            2006