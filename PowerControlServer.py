from controllers.RelayControl import RelayControl
from controllers.SwitchMonitor import SwitchMonitor
import WebSocket
import Socket
import threading

class PowerControlServer:
    def __init__(self):
        self.WebSocket = WebSocket
        self.Socket = Socket
        self.RelayControl = RelayControl()
        self.SwitchMonitor = SwitchMonitor()

    def run(self):
        print("Starting server...")
        app_status = "Starting..."

        # Set up threads
        ws_thread = threading.Thread(target=startwebsocketserver, args=[])
        soc_thread = threading.Thread(target=startsocketserver, args=[])
        switchmon_thread = threading.Thread(target=startSwitchMonitor)

        print("Starting socket threads...")
        ws_thread.start()
        soc_thread.start()

        print("Starting switch monitor...")
        switchmon_thread.start()

        print("Server Running")
        app_status = "Running"

    def stop(self):
        print("Stopping Power Control Service...")
        try:
            self.RelayControl.cleanup()
            self.SwitchMonitor.cleanup()
        except:
            pass

        return 0
    
def startSwitchMonitor():
    sm = SwitchMonitor()
    sm.run()

def startsocketserver():
    Socket.run()

def startwebsocketserver():
    WebSocket.run()

