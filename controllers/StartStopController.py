from threading import Thread 
from controllers.RelayControl import RelayControl
from MessageBroker import MessageBroker
from controllers.InterlockController import InterlocksController
from devices.Projector import Projector
from devices.Dolby import Dolby
from time import sleep

class StartStopController: 
    _instance = None
    _running = False

    # Singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create the instance only if it doesn't already exist
            cls._instance = super(StartStopController, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'): 
            self.initialized = True
            self.RelayController = RelayControl()
            self.MessageBroker = MessageBroker()
            self.Interlocks = InterlocksController()
            self.projector = Projector()
            self.dolby = Dolby()

## TODO: projector.standby() is being called even though PlaybackInterlock is true.  Figure out why
    def startThread(self, callback=None):
        self._running = True 
        self.Interlocks.setLockout(True)
        print("Startup process beginning...")
        # get relay info and turn on if it's off
        if self.RelayController.getLightsRelay() == False: 
            self.RelayController.setLights(1)
            sleep(2)
        
        if self.RelayController.getAmpsRelay() == False: 
            self.RelayController.setAmps(1)
            sleep(2)
        
        if self.RelayController.getAVEquipmentRelay() == False: 
            self.RelayController.setAVEquipment(1)
            sleep(2)
        
        if self.RelayController.getExhaustFanRelay() == False: 
            self.RelayController.setExhaustFan(1)
            sleep(2)

        if self.RelayController.getProjectorRelay() == False: 
            self.RelayController.setProjector(1)

        # Wait for 3 minutes, then turn projector on 
        sleep(10)
        self.projector.powerup()

        # Clear locks
        self._running = False
        self.Interlocks.setLockout(False)
        print("Startup Complete.")
        if callback: 
            callback(0)
        # return 0

    def stopThread(self, callback=None): 
        self._running = True
        self.Interlocks.setLockout(True)

        print("Shutdown process beginning...")
        # if something is being played back, do not shut things down
        pInterlock = self.Interlocks.getInterlocks()
        if pInterlock["PlaybackInterlock"] == True:
            self._running = False
            self.Interlocks.setLockout(False)
            print("Playback interlock [ACTIVE]")
            if callback:
                callback(-2)
            return -1
        else: 
            # can shut off everything except AV and exhaust/projector relays: 
            self.RelayController.setLights(0)
            sleep(2)
            self.RelayController.setAmps(0)
            sleep(2)

            # Assess power levels first
            pPower = self.projector.getPower() # int: 3 - Standby, 0 - Ready, 1 - Full Power (Lamp on)
            sPower = self.dolby.getBooted()    # true if on, false if inaccessible

            # Deal with IMS 
            if(sPower == True): 
                self.dolby.shutdown()
                sleep(180)

            # Deal with projector
            if(pPower == 1): 
                timeout = 0
                self.projector.standby()
                # loop until cooldown is finished.  Projector takes a second to register cooldown countdown
                sleep(5)
                while(True): 
                    cooldown = self.projector.getCooldown()
                    print("Projector Cooldown: " + str(cooldown))
                    if(cooldown != 0):
                        sleep(5)
                    elif(cooldown == 0): 
                        break
                    else:
                        # catches any missed responses from projector
                        sleep(5)
                        if(timeout == 15): 
                            break
                        timeout += 1 # make sure shutdown process doesn't hang
                # cooldown is finished
                sleep(60)

            else:
                # Someone else requested projector power 0 or 3. Need to check if there's a cooldown active
                cd = self.projector.getCooldown()
                if(cd != 0): 
                    # loop and do nothing until cooldown is finished
                    timeout = 0
                    while(True): 
                        cd = self.projector.getCooldown()
                        if(cd == 0): 
                            break
                        else: 
                            sleep(5)
                            if(timeout == 15): 
                                break
                            timeout += 1
                else: 
                    # no cooldown, we can proceed normally
                    sp = self.dolby.getBooted()
                    if(sp == True): 
                        self.dolby.shutdown()
                        sleep(180)
                        self.projector.standby()
                        sleep(60)
                    elif(sp == False): 
                        # Server is off, we can proceed
                        self.projector.standby()
                        sleep(60)

            sleep(5)
            # Confirm that stuff is in expected state
            p = self.projector.getPower()
            s = self.dolby.getBooted()
            if(p == 3 and s == False):
                # Safe to shut relays off
                self.RelayController.setExhaustFan(0)
                sleep(2)
                self.RelayController.setProjector(0)
            else: 
                # Should never get to this if stuff is working correctly
                print("Error: Projector and server are not in expected state.  Cannot continue shutdown")
                self._running = False
                self.Interlocks.setLockout(False)
                if callback: 
                    callback(-1)
                return -1                       

        self._running = False
        self.Interlocks.setLockout(False)
        print("Shutdown Complete.")
        if callback:
            callback(0)
        # return 0

    def stop(self, callback=None): 
        if self._running == True: 
            if callback: 
                callback(-1)
            else:
                return -1
        else:     
            t = Thread(target=self.stopThread, args=(callback,))
            t.start()

    def start(self, callback=None): 
        if self._running == True:
            if callback:
                callback(-1)
            else: 
                return -1
        else: 
            t = Thread(target=self.startThread, args=(callback,))
            t.start()

    def getRunning(self): 
        return self._running
