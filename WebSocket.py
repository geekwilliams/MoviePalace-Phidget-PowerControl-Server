import tornado.ioloop
import tornado.web
import tornado.websocket
import json
import Globals
from MessageBroker import MessageBroker
from controllers.RelayControl import RelayControl
from controllers.SwitchMonitor import SwitchMonitor
from controllers.StartStopController import StartStopController
import uuid

connected_clients = set()

class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.rc = RelayControl()
        self.switchMonitor = SwitchMonitor()
        self.relayDetail = RelayDetail()
        self.switchDetail = SwitchDetail()
        self.MessageBroker = MessageBroker()
        self.id = str(uuid.uuid4())
        #print("Websocket MessageBroker id: {}".format(id(self.MessageBroker)))

    def __eq__(self, other):
        return isinstance(other, WebSocketHandler) and self.id == other.id

    def __hash__(self):
        return hash(self.id)  # To allow use in sets or as dict keys
    
    def check_origin(self, origin):
        # Allow all origins (for development purposes)
        return True

        # For production, restrict allowed origins
        # allowed_origins = ["http://example.com", "http://your-angular-app-domain.com"]
        # return origin in allowed_origins

    def open(self):
        connected_clients.add(self)
        self.MessageBroker.add_websocket(self)  # this class tracks all clients to send broadcasts to

    def on_message(self, message):
        try: 
            data = json.loads(message)
            if data["Message"] == "":
                pass
            elif data["Content"] == "get-status":
                self.write_message(json.dumps(self.getStatus()))

            elif data["Content"] == "get-switches":
                self.write_message(json.dumps(self.getSwitchStatus()))

            elif data["Number"] == 2003:
                # Parse request content
                content = data["Content"]
                relay = content.split(":")[0]
                relayState = content.split(":")[1]
                if relay == "Lights":
                    status = self.rc.setLights(bool2int(relayState))
                    if status != 0:
                        # RelayController will send broadcast message out if update is successful.  Otherwise we need to handle the error
                        response = json.dumps({"Message": "RelayStateChangeError", "Number": 2003, "Content": "Could not change Relay due to internal error"})
                        self.write_message(response)

                elif relay == "Amps":
                    status = self.rc.setAmps(bool2int(relayState))
                    if status != 0:
                        response = json.dumps({"Message": "RelayStateChangeError", "Number": 2003, "Content": "Could not change Relay due to internal error"})
                        self.write_message(response)

                elif relay == "AVEquipment": 
                    status = self.rc.setAVEquipment(bool2int(relayState))
                    if status != 0:
                        response = json.dumps({"Message": "RelayStateChangeError", "Number": 2003, "Content": "Could not change Relay due to internal error"})
                        self.write_message(response)

                elif relay == "ExhaustFan":
                    status = self.rc.setExhaustFan(bool2int(relayState))
                    if status != 0:
                        response = json.dumps({"Message": "RelayStateChangeError", "Number": 2003, "Content": "Could not change Relay due to internal error"})
                        self.write_message(response)

                elif relay == "Projector": 
                    status = self.rc.setProjector(bool2int(relayState))
                    if status != 0:
                        response = json.dumps({"Message": "RelayStateChangeError", "Number": 2003, "Content": "Could not change Relay due to internal error"})
                        self.write_message(response) 
            elif data["Number"] == 2005: 
                # Callback for operations
                def cb(i): 
                    if i == 0: 
                        response = json.dumps({"Message": "Success", "Number": 2005, "Content": "Procedure Successfull"})
                    elif i == -1: 
                        response = json.dumps({"Message": "Failure", "Number": 2005, "Content": "Procedure Unsuccessful"})
                    try: 
                        # write_message comes in from self, which is provided by the closure of the cb function (it comes from higher scope)
                        self.write_message(response)
                    except Exception as e: 
                        print(e)

                if data["Content"] == "startup":  
                    scController = StartStopController()
                    scController.start(callback=cb)
                elif data["Content"] == "shutdown": 
                    scController = StartStopController()
                    scController.stop(callback=cb)

            else: 
                self.write_message(json.dumps({"Message": "OperationNotSupportedError", "Number": None, "Content": "Requested operation is not supported"}))
        except: 
            self.write_message(json.dumps({"Message": "UndefinedError", "Number": None, "Content": "An unknown error occurred."}))

    def getStatus(self):
        detail = {"PowerControlName": Globals.auditorium_info, "ScheduleMode": False, "Lights": self.relayDetail["Lights"], "Amps": self.relayDetail["Amps"], "AVEquipment": self.relayDetail["AVEquipment"], "ExhaustFan": self.relayDetail["ExhaustFan"], "Projector": self.relayDetail["Projector"]}
        response = { "Message": "Reply Message", "Number": 2001, "Content": "{0}".format(json.dumps(detail))}
        return response
    
    def getSwitchStatus(self):
        detail = {"PowerControlName": Globals.auditorium_info, "ScheduleMode": False, "Lights": self.switchDetail["Lights"], "Amps": self.switchDetail["Amps"], "AVEquipment": self.switchDetail["AVEquipment"], "ExhaustFan": self.switchDetail["ExhaustFan"], "Projector": self.switchDetail["Projector"]}
        response = { "Message": "Reply Message", "Number": 2004, "Content": "{0}".format(json.dumps(detail))}
        return response

    def on_close(self):
        connected_clients.remove(self)
        self.MessageBroker.remove_websocket(self) 

    def broadcast_message(self, message):
        # Send message on switch or relay status change
        for client in connected_clients:
            try: 
                if isinstance(client, WebSocketHandler):
                    client.write_message(message)
            except tornado.websocket.WebSocketClosedError:
                connected_clients.remove(client)

def run(port=8081):
    application = tornado.web.Application([(r"/", WebSocketHandler)])
    application.listen(port)
    print("Websocket server running on port {}".format(port))
    tornado.ioloop.IOLoop.current().start()


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
        
def bool2int(bool):
    if bool.lower() == "false": 
        return 0
    elif bool.lower() == "true":
        return 1
    

