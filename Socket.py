import select
import socket
from controllers.RelayControl import RelayControl
import Globals
from datetime import datetime
import json
from MessageBroker import MessageBroker
from controllers.SwitchMonitor import SwitchMonitor
from controllers.StartStopController import StartStopController
from controllers.InterlockController import InterlocksController

class SocketHelper:
    def __init__(self, host='0.0.0.0', port=5001):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.port)
        self.server_socket.setblocking(False)  # Non-blocking socket
        self.inputs = [self.server_socket]  # List of sockets to monitor for incoming connections
        self.rc = RelayControl()
        self.MessageBroker = MessageBroker()
        self.sm = SwitchMonitor()
        self.rd = RelayDetail()
        self.interlocks = InterlocksController()
    
    def run(self):

        print("Socket server listening on {0}:{1}".format(self.host, self.port))
        try:
            while True:
                readable, _, exceptional = select.select(self.inputs, [], self.inputs)
                
                for s in readable:
                    if s is self.server_socket:
                        # New connection
                        conn, addr = self.server_socket.accept()
                        # print("Connected by {0}".format(addr))
                        conn.setblocking(False)
                        self.inputs.append(conn)  # Add new connection to inputs list
                        self.MessageBroker.add_socket(conn) # Add connection to list for MessagePump
                    else:
                        # Existing connection has data to read
                        data = s.recv(1024)
                        if data:
                            message = data.decode('utf-8').strip()
                            if message == "status":
                                response = "Lights:{0},Amps:{1},AVEquipment:{2},ExhaustFan:{3},Projector:{4}\n".format(self.rc.getLightsRelay(), self.rc.getAmpsRelay(),self.rc.getAVEquipmentRelay(),self.rc.getExhaustFanRelay(),self.rc.getProjectorRelay())
                            
                            elif message == "info":
                                response = "Host:phidget,AppVersion:{0},SystemTime:\"{1}\"\n".format(Globals.app_version, datetime.now())

                            elif message == "help":
                                response = "\nstatus\ninfo\nhelp\ngetswitches\nsetrelay:<relayname>:<bool>\ngetinterlocks\ndevicestatus\nstartup\nshutdown\n"

                            elif message == "relays":
                                response = "\nLights\nAmps\nAVEquipment\nExhaustFan\nProjector\n"

                            elif message.split(":")[0] == "schedulemode":
                                response = "Schedule mode is no longer available.\n"

                            elif message.split(":")[0] == "setrelay": 
                                t = message.split(":")
                                try: 
                                    relay = t[1]
                                    relayok = False
                                    stateok = False
                                    relayState = t[2]

                                    # if relay != "Lights" or relay != "Amps" or relay != "AVEquipment" or relay != "ExhaustFan" or relay != "Projector":
                                    #     response = "Incorrect relay specified.  Please try again\n"
                                    # else: 
                                    #     relayok = True

                                    if relayState == "true" or relayState == "false":
                                        pass
                                    else:
                                        response = "Incorrect relay state specified.  Must be true/false\n"

                                    # Set relays
                                    if relay == "Lights":
                                        if self.interlocks.getControlsLockout(): 
                                            response = "Controls lockout [ACTIVE]\n"
                                        else: 
                                            status = self.rc.setLights(bool2int(relayState))
                                            if status == 0:
                                                response = None
                                            elif status == 1: 
                                                response = "Unable to set Lights relay due to unknown exception.\n"
                                            elif status == -1:
                                                response = "Lights relay not set due to active interlock.\n"

                                    elif relay == "Amps":
                                        if self.interlocks.getControlsLockout():
                                            response = "Controls lockout [ACTIVE]\n"
                                        else:
                                            status = self.rc.setAmps(bool2int(relayState))
                                            if status == 0:
                                                response = None 
                                            elif status == 1: 
                                                response = "Unable to set Amps relay due to unknown exception.\n"
                                            elif status == -1:
                                                response = "Amps relay not set due to active interlock.\n"

                                    elif relay == "AVEquipment": 
                                        if self.interlocks.getControlsLockout():
                                            response = "Controls lockout [ACTIVE]n"
                                        else: 
                                            status = self.rc.setAVEquipment(bool2int(relayState))
                                            if status == 0:
                                                response = None 
                                            elif status == 1: 
                                                response = "Unable to set AVEquipment relay due to unknown exception.\n"
                                            elif status == -1:
                                                response = "AVEquipment relay not set due to active interlock.\n"

                                    elif relay == "ExhaustFan": 
                                        if self.interlocks.getControlsLockout():
                                            response = "Controls lockout [ACTIVE]\n"
                                        else: 
                                            status = self.rc.setExhaustFan(bool2int(relayState))
                                            if status == 0:
                                                response = None
                                            elif status == 1: 
                                                response = "Unable to set ExhaustFan relay due to unknown exception.\n"
                                            elif status == -1:
                                                response = "ExhaustFan relay not set due to active interlock.\n"

                                    elif relay == "Projector": 
                                        if self.interlocks.getControlsLockout():
                                            response = "Controls lockout [ACTIVE]\n"
                                        else: 
                                            status = self.rc.setProjector(bool2int(relayState))
                                            if status == 0:
                                                response = None 
                                            elif status == 1: 
                                                response = "Unable to set Projector relay due to unknown exception.\n"
                                            elif status == -1:
                                                response = "Projector relay not set due to active interlock.\n"
                                    else:
                                        response = "Specified relay not found.  Please check your command and try again"
                                except: 
                                    pass


                            elif message == "getswitches":
                                st = self.sm.getSwitchStatus()
                                ss = st["Content"]
                                m = ""
                                for key in ss: 
                                    m += (key + ":" + ss[key] + ",")

                                response = m.rstrip(",") + "\n"
                            
                            elif message == "getinterlocks": 
                                i = self.interlocks.getInterlocks()
                                st = ""
                                for key in i: 
                                    st +=(key + ":" + bool2string(i[key]) + ",")
                                response = st.rstrip(",") + "\n"

                            elif message == "devicesstatus": 
                                i = self.interlocks.getDeviceStatus()
                                st = ""
                                for key in i: 
                                    st +=(key + ":" + bool2string(i[key]) + ",")
                                response = st.rstrip(",") + "\n"
                            
                            elif message == "startup": 
                                response = None
                                def startcb(i): 
                                    if i == 0: 
                                        m = "Startup successful\n"
                                    elif i == -1: 
                                        m = "Startup failed due to unknown error\n"
                                    s.sendall(m.encode())
                                sbController = StartStopController()
                                sbController.start(callback=startcb)
                            
                            elif message == "shutdown": 
                                response = None
                                def stopcb(i): 
                                    if i == 0: 
                                        m = "Shutdown successful\n"
                                    elif i == -1: 
                                        m = "Shutdown failed due to error\n"
                                    elif i == -2: 
                                        m = "Shutdown failed because playback interlock is active\n"
                                    s.sendall(m.encode())
                                sbController = StartStopController()
                                sbController.stop(callback=stopcb)

                            else:
                                response = "Not a valid command\n"

                            if response != None:
                                s.sendall(response.encode())
                                pass
                        else:
                            # Client disconnected
                            print("Closing connection.")
                            self.inputs.remove(s)
                            s.close()
                        
                for s in exceptional:
                    #print("Handling exceptional condition.")
                    self.inputs.remove(s)
                    s.close()
        except KeyboardInterrupt:
            print("Server shutting down.")

    def broadcast(self, message, sender_socket=None):
        # Set broadcast to send message if switch or relay state changes
        for s in self.inputs: 
            if s is not self.server_socket and s is not sender_socket:
                try:
                    s.sendall(message.encode('utf-8'))
                except: 
                    self.inputs.remove(s)
                    s.close() 

    def getStatus(self):
        detail = {"PowerControlName": Globals.auditorium_info, "ScheduleMode": False, "Lights": self.rd["Lights"], "Amps": self.rd["Amps"], "AVEquipment": self.rd["AVEquipment"], "ExhaustFan": self.rd["ExhaustFan"], "Projector": self.rd["Projector"]}
        response = { "Message": "Reply Message", "Number": 2001, "Content": "{0}".format(detail)}
        return response

    def getSwitchStatus(self):
        detail = {"PowerControlName": Globals.auditorium_info, "ScheduleMode": False, "Lights": SwitchDetail["Lights"], "Amps": SwitchDetail["Amps"], "AVEquipment": SwitchDetail["AVEquipment"], "ExhaustFan": SwitchDetail["ExhaustFan"], "Projector": SwitchDetail["Projector"]}
        response = { "Message": "Reply Message", "Number": 2004, "Content": "{0}".format(detail)}
        return response
    

def bool2int(bool):
    if bool.lower() == "false": 
        return 0
    elif bool.lower() == "true":
        return 1
    
def int2bool(int):
    if int == 1:
        return "true"
    elif int == 0:
        return "false"
def bool2string(bool): 
    if bool == True:
        return "true"
    elif bool == False:
        return "false"
    
def run():
    server = SocketHelper()
    server.run()

class SwitchDetail:
    def __init__(self):
        self.rc = SwitchMonitor()

    def __getitem__(self, key):
        if key == "Lights":
            return self.rc.getLightsSwitch()
        elif key == "Amps":
            return self.rc.getAmpsSwitch()
        elif key == "AVEquipment":
            return self.rc.getAVEquipmentSwitch()
        elif key == "ExhaustFan":
            return self.rc.getExhaustFanSwitch()
        elif key == "Projector":
            return self.rc.getProjectorSwitch()
        elif key == "PowerControlName":
            return Globals.auditorium_info
        elif key == "ScheduleMode":
            return False
        else:
            raise KeyError("{} not found".format(key))
        
class RelayDetail: 
    def __init__(self):
        self.rc = RelayControl()

    def __getitem__(self, key):
        if key == "Lights":
            return self.rc.getLightsRelay()
        elif key == "Amps":
            return self.rc.getAmpsRelay()
        elif key == "AVEquipment":
            return self.rc.getAVEquipmentRelay()
        elif key == "ExhaustFan":
            return self.rc.getExhaustFanRelay()
        elif key == "Projector":
            return self.rc.getProjectorRelay()
        elif key == "PowerControlName":
            return Globals.auditorium_info
        elif key == "ScheduleMode":
            return False
        else:
            raise KeyError("{} not found".format(key))

if __name__ == '__main__':
    server = SocketHelper()
    print("Socket server running on port {}".format(server.port))
    server.run()
