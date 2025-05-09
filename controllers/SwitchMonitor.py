from Phidget22.Devices.VoltageInput import *
from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
import traceback
import Globals
from MessageBroker import MessageBroker
import time


class SwitchMonitor:
    _instance = None

    switchLights = VoltageInput()
    switchAmps = VoltageInput()
    switchAVEquipment = VoltageInput()
    switchExhaustFan = VoltageInput()
    switchProjector = VoltageInput()
    runvar = True

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create the instance only if it doesn't already exist
            cls._instance = super(SwitchMonitor, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.initialized = True
            self.MessageBroker = MessageBroker()
            self.SwitchDetail = SwitchDetail()
            try: 

                self.switchLights.setChannel(0)
                self.switchAmps.setChannel(1)
                self.switchAVEquipment.setChannel(2)
                self.switchExhaustFan.setChannel(3)
                self.switchProjector.setChannel(4)

                self.switchLights.openWaitForAttachment(5000)
                self.switchAmps.openWaitForAttachment(5000)
                self.switchAVEquipment.openWaitForAttachment(5000)
                self.switchExhaustFan.openWaitForAttachment(5000)
                self.switchProjector.openWaitForAttachment(5000)

                # Event handlers
                # self.switchLights.setOnVoltageChangeHandler(self.onVoltageChange)
                # self.switchAmps.setOnVoltageChangeHandler(self.onVoltageChange)
                # self.switchAVEquipment.setOnVoltageChangeHandler(self.onVoltageChange)
                # self.switchExhaustFan.setOnVoltageChangeHandler(self.onVoltageChange)
                # self.switchProjector.setOnVoltageChangeHandler(self.onVoltageChange)

                # # Voltage thresholds to prevent excessive message traffic
                # self.switchLights.setVoltageChangeTrigger(1)
                # self.switchLights.setDataInterval(500)
                # self.switchAmps.setVoltageChangeTrigger(1)
                # self.switchAmps.setDataInterval(500)
                # self.switchAVEquipment.setVoltageChangeTrigger(1)
                # self.switchAVEquipment.setDataInterval(500)
                # self.switchExhaustFan.setVoltageChangeTrigger(1)
                # self.switchExhaustFan.setDataInterval(500)
                # self.switchProjector.setVoltageChangeTrigger(1)
                # self.switchProjector.setDataInterval(500)


            except PhidgetException as ex: 
                traceback.print_exc()
                print("")
                print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)

    # thread entry point
    def run(self):
        while(self.runvar):
            lightSwitch = self.getLightsSwitch()
            ampSwitch = self.getAmpsSwitch()
            avSwitch = self.getAVEquipmentSwitch()
            exSwitch = self.getExhaustFanSwitch()
            pSwitch = self.getProjectorSwitch()

            # rest the thread so we don't overwhelm resources
            time.sleep(0.25)
            
            # Check for change in any switches and send message if there's a change
            if(lightSwitch != self.getLightsSwitch()):
                self.sendMessage()
            if(ampSwitch != self.getAmpsSwitch()):
                self.sendMessage()
            if(avSwitch != self.getAVEquipmentSwitch()):
                self.sendMessage()
            if(exSwitch != self.getExhaustFanSwitch()):
                self.sendMessage()
            if(pSwitch != self.getProjectorSwitch()):
                self.sendMessage()
                


    def cleanup(self):
        # Stop the main loop 
        self.runvar = False
        try: 
            self.switchLights.close()
            self.switchAmps.close()
            self.switchAVEquipment.close()
            self.switchExhaustFan.close()
            self.switchProjector.close()
        except PhidgetException as ex: 
            traceback.print_exc()
            print("")
            print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)

    def onVoltageChange(self, integ, voltage):
        # On change exceeding set threshold of 1V, add message to broadcast queue, then broadcast to connected clients
        # MessageBroker will format message appropriatly for client connection
        # Number for switch status is always 2006
        if int(voltage) == 5:
            # switch is on Auto
            message = {"Message": "Trigger Update", "Number": 2006}
            message["msg"] = { "LightsSwitch": self.SwitchDetail["Lights"], "AmpsSwitch": self.SwitchDetail["Amps"], "AVEquipmentSwitch": self.SwitchDetail["AVEquipment"], "ExhaustFanSwitch": self.SwitchDetail["ExhaustFan"], "ProjectorSwitch": self.SwitchDetail["Projector"]}
            self.MessageBroker.ws_post_message(message)

        elif int(voltage) == 4: 
            # switch is on manual
            message = {"Message": "Trigger Update", "Number": 2006}
            message["msg"] = { "LightsSwitch": self.SwitchDetail["Lights"], "AmpsSwitch": self.SwitchDetail["Amps"], "AVEquipmentSwitch": self.SwitchDetail["AVEquipment"], "ExhaustFanSwitch": self.SwitchDetail["ExhaustFan"], "ProjectorSwitch": self.SwitchDetail["Projector"]}
            self.MessageBroker.ws_post_message(message)
            
        elif int(voltage) == 0: 
            # switch is off
            message = {"Message": "Trigger Update", "Number": 2006}
            message["msg"] = { "LightsSwitch": self.SwitchDetail["Lights"], "AmpsSwitch": self.SwitchDetail["Amps"], "AVEquipmentSwitch": self.SwitchDetail["AVEquipment"], "ExhaustFanSwitch": self.SwitchDetail["ExhaustFan"], "ProjectorSwitch": self.SwitchDetail["Projector"]}
            self.MessageBroker.ws_post_message(message)

        # do nothing if we measure a transition voltage (anything besides 5, 4 or 0)

    def getLightsSwitch(self):
        return getSwitchState(self.switchLights.getVoltage())
    
    def getAmpsSwitch(self):
        return getSwitchState(self.switchAmps.getVoltage())
    
    def getAVEquipmentSwitch(self):
        return getSwitchState(self.switchAVEquipment.getVoltage())
    
    def getExhaustFanSwitch(self):
        return getSwitchState(self.switchExhaustFan.getVoltage())
    
    def getProjectorSwitch(self):
        return getSwitchState(self.switchProjector.getVoltage())
    
    def sendMessage(self):
        # only the UI is updated with switch status
        message = {"Message": "Switch Update", "Number": 2006}
        message["msg"] = { "LightsSwitch": self.SwitchDetail["Lights"], "AmpsSwitch": self.SwitchDetail["Amps"], "AVEquipmentSwitch": self.SwitchDetail["AVEquipment"], "ExhaustFanSwitch": self.SwitchDetail["ExhaustFan"],  "ProjectorSwitch": self.SwitchDetail["Projector"] }
        self.MessageBroker.ws_post_message(message)
    
    def getSwitchStatus(self):
        detail = {"Lights": self.SwitchDetail["Lights"], "Amps": self.SwitchDetail["Amps"], "AVEquipment": self.SwitchDetail["AVEquipment"], "ExhaustFan": self.SwitchDetail["ExhaustFan"], "Projector": self.SwitchDetail["Projector"]}
        response = { "Message": "Reply Message", "Number": 2004, "Content": detail}
        return response

def getSwitchState(voltage):
    if(voltage >= 5.000):
        return "auto"
    elif(voltage < 5 and voltage > 1):
        return "manual"
    elif(voltage < 1):
        return "off"
    
    
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