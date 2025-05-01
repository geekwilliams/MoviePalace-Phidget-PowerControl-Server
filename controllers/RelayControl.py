from Phidget22.PhidgetException import *
from Phidget22.Phidget import *
from Phidget22.Devices.DigitalOutput import *
from Phidget22.Devices.VoltageInput import *
import traceback
import os
import Globals
from MessageBroker import MessageBroker
from controllers.InterlockController import InterlocksController

class RelayControl:
    _instance = None

    relayLights = DigitalOutput()
    relayAmps = DigitalOutput()
    relayAVEquipment = DigitalOutput()
    relayExhaustFan = DigitalOutput()
    relayProjector = DigitalOutput()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create the instance only if it doesn't already exist
            cls._instance = super(RelayControl, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.initialized = True
            try:
                self.relayLights.setChannel(0)
                self.relayAmps.setChannel(1)
                self.relayAVEquipment.setChannel(2)
                self.relayExhaustFan.setChannel(3)
                self.relayProjector.setChannel(4)

                self.relayLights.setOnErrorHandler(RelayControl.onError)
                self.relayAmps.setOnErrorHandler(RelayControl.onError)
                self.relayAVEquipment.setOnErrorHandler(RelayControl.onError)
                self.relayExhaustFan.setOnErrorHandler(RelayControl.onError)
                self.relayProjector.setOnErrorHandler(RelayControl.onError)

                self.relayLights.openWaitForAttachment(5000)
                self.relayAmps.openWaitForAttachment(5000)
                self.relayAVEquipment.openWaitForAttachment(5000)
                self.relayExhaustFan.openWaitForAttachment(5000)
                self.relayProjector.openWaitForAttachment(5000)

                # If we made it here then things are OK and we can proceed
                self.interlocks = InterlocksController()
                self.mb = MessageBroker()

                # Restore relay state from last app run if it exists
                try: 
                    with open("db", "rb") as f: 
                        data = f.read()
                        i = 0
                        for i in range(5): 
                            # ignore interlocks if they're active at app start for some reason
                            if i == 0: 
                                self.relayLights.setDutyCycle(data[0])
                            elif i == 1: 
                                self.relayAmps.setDutyCycle(data[1])
                            elif i == 2: 
                                self.relayAVEquipment.setDutyCycle(data[2])
                            elif i == 3: 
                                self.relayExhaustFan.setDutyCycle(data[3])
                            elif i == 4: 
                                self.relayProjector.setDutyCycle(data[4])

                except IOError: 
                    with open("db", "wb") as f: 
                        # initializes all relays to off 
                        f.write(b'\x00' * 5)
                
            except PhidgetException as ex: 
                traceback.print_exc()
                print("")
                print("PhidgetException " + str(ex.code) + " (" + ex.description + "): " + ex.details)
        
    def onError(self, code, description):
        print("Code: " + ErrorEventCode.getName(code))
        print("Description: " + str(description))
    
    def cleanup(self):
        self.relayLights.close()
        self.relayAmps.close()
        self.relayAVEquipment.close()
        self.relayExhaustFan.close()
        self.relayProjector.close()
    
    def setLights(self, i):
        # if self.interlocks.getLockout(): 
        #     print("Warning: Controls lockout [ACTIVE]")
        #     return -2
       
        if i == 0 and self.interlocks.getPlaybackInterlock() == True: 
            print("Warning: Lights relay not changed due to interlock status (ACTIVE)")
            return -1
    
        else: 
            try:
                self.relayLights.setDutyCycle(i)
                self.updateRelayStateReg(0, i)
                msg = getStatus()
                # Override
                msg["Number"] = 2003
                self.mb.add_message(msg)
                self.mb.broadcast()
                return 0
            except Exception as e:
                print("Error: Couldn't set Lights relay")
                print(e)
                traceback.print_exc()
                return 1
    
    def setAmps(self, i):
        # if self.interlocks.getLockout(): 
        #     print("Warning: Controls lockout [ACTIVE]")
        #     return -2
        
        if i == 0 and self.interlocks.getPlaybackInterlock() == True:
            print("Warning: Amps relay not changed due to interlock status (ACTIVE)")
            return -1
            
        else: 
            try: 
                self.relayAmps.setDutyCycle(i)
                self.updateRelayStateReg(1, i)
                msg = getStatus()
                # Override
                msg["Number"] = 2003
                self.mb.add_message(msg)
                self.mb.broadcast()
                return 0
            except:
                print("Error: Couldn't set Amps relay")
                return 1

    def setAVEquipment(self, i):
        # if self.interlocks.getLockout(): 
        #     print("Warning: Controls lockout [ACTIVE]")
        #     return -2
        
        if i == 0 and self.interlocks.getAVInterlock() == True: 
            print("Warning: AVEquipment relay not changed due to interlock status (ACTIVE)")
            return -1
        
        else: 
            try: 
                self.relayAVEquipment.setDutyCycle(i)
                self.updateRelayStateReg(2, i)
                msg = getStatus()
                msg["Number"] = 2003
                self.mb.add_message(msg)
                self.mb.broadcast()
                return 0
            except:
                print("Error: Couldn't set AVEquipment relay")
                return 1
        
    def setExhaustFan(self, i):
        # if self.interlocks.getLockout(): 
        #     print("Warning: Controls lockout [ACTIVE]")
        #     return -2
        
        if i == 0 and self.interlocks.getLampInterlock() == True: 
            print("Warning: Exhaust relay not changed due to interlock status (ACTIVE)")
            return -1
                
        else: 
            try: 
                self.relayExhaustFan.setDutyCycle(i)
                self.updateRelayStateReg(3, i)
                msg = getStatus()
                # Override
                msg["Number"] = 2003
                self.mb.add_message(msg)
                self.mb.broadcast()
                return 0
            except:
                print("Error: Couldn't set Exhaust fan relay")
                return 1

    # handle all three active states with interlock 
    def setProjector(self, i):
        # if self.interlocks.getLockout(): 
        #     print("Warning: Controls lockout [ACTIVE]")
        #     return -2
        if i == 0 and self.interlocks.getLampInterlock() == True and self.interlocks.getServerInterlock() == True: 
            print("Warning: Projector relay not changed due to multiple interlocks (ACTIVE)")
            return -1
        elif i == 0 and self.interlocks.getServerInterlock() == True and self.interlocks.getLampInterlock() == False: 
            print("Warning: Projector relay not changed due to server interlock (ACTIVE)")
            return -1
        elif i == 0 and self.interlocks.getLampInterlock() == True and self.interlocks.getServerInterlock() == False: 
            print("Warning: Projector relay not changed due to lamp interlock (ACTIVE)")
            return -1
        else: 
            try: 
                self.relayProjector.setDutyCycle(i)
                self.updateRelayStateReg(4, i)
                msg = getStatus()
                # Override
                msg["Number"] = 2003
                self.mb.add_message(msg)
                self.mb.broadcast()
                return 0
            except:
                print("Error: Couldn't set projector relay")
                return 1

    def getLightsRelay(self):
        return getRelayState(self.relayLights.getDutyCycle())
    
    def getAmpsRelay(self):
        return getRelayState(self.relayAmps.getDutyCycle())
    
    def getAVEquipmentRelay(self):
        return getRelayState(self.relayAVEquipment.getDutyCycle())
    
    def getExhaustFanRelay(self):
        return getRelayState(self.relayExhaustFan.getDutyCycle())
    
    def getProjectorRelay(self):
        return getRelayState(self.relayProjector.getDutyCycle())
    
    def updateRelayStateReg(self, index, newState):
        # 0 - Lights
        # 1 - Amps
        # 2 - AVEquipment
        # 3 - Exhaust Fan
        # 4 - Projector
        filepath = "db"
        with open(filepath, "r+b") as f: 
            f.seek(index)
            current = f.read(1)
            if current and current [0] != newState: 
                f.seek(index)
                f.write(bytes(newState))
                f.flush()
                os.fsync(f.fileno())
    
    def getRelayStateReg(self, index):
        with open("db") as f:
            f.seek(index)
            return f.read(1) 



    
def getRelayState(int):
    if(int == 1): return True
    else:         return False
        
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
        
def getStatus():
    # Default:  Message number can be changed for relay changes
    rc = RelayDetail()
    detail = {"PowerControlName": Globals.auditorium_info, "Lights": rc["Lights"], "Amps": rc["Amps"], "AVEquipment": rc["AVEquipment"], "ExhaustFan": rc["ExhaustFan"], "Projector": rc["Projector"]}
    response = { "Message": "Reply Message", "Number": 2001, "msg": detail}
    return response


