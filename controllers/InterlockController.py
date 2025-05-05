# This class will communicate with devices and determine what to set the interlock state to, then monitor for changes
import threading
import time
from devices.Projector import Projector
from devices.Dolby import Dolby
from MessageBroker import MessageBroker

class InterlocksController:
    _lampInterlock = False
    _serverInterlock = False
    _playbackInterlock = False
    _avInterlock = True
    _lockout = False
    _projectorOnline = False
    _projectorPower = -1
    _serverOnline = False
    _serverBooted = False
    _playbackState = "offline"
    _startStopStatus = ""

    _instance = None

    #singleton
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # Create the instance only if it doesn't already exist
            cls._instance = super(InterlocksController, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):  # Prevent re-initialization
            self.initialized = True
            self.MessageBroker = MessageBroker()
            self.projector = Projector()
            self.dolby = Dolby()
            self.id = InterlocksDetail()

    def getInterlocks(self):
        return { "LampInterlock": self.id["LampInterlock"],"PlaybackInterlock": self.id["PlaybackInterlock"], "ServerInterlock": self.id["ServerInterlock"], "AVInterlock": self.id["AVInterlock"], "ControlsLockout": self.id["ControlsLockout"] }
        
    def getDeviceStatus(self):
        return { "ProjectorOnline": self.id["ProjectorOnline"], "ServerOnline": self.id["ServerOnline"],"ServerBooted": self.id["ServerBooted"], "PlaybackState": self.id["PlaybackState"], "ProjectorPowerLevel": self.id["ProjectorPowerLevel"] }
    
    def getLampInterlock(self): 
        return self._lampInterlock
    
    def getPlaybackInterlock(self): 
        return self._playbackInterlock
    
    def getServerInterlock(self): 
        return self._serverInterlock
    
    def getAVInterlock(self): 
        return self._avInterlock
    
    def getProjectorOnline(self): 
        return self._projectorOnline
    
    def getProjectorPower(self): 
        return self._projectorPower
    
    def getServerOnline(self): 
        return self._serverOnline
    
    def getServerBooted(self): 
        return self._serverBooted
    
    def getPlaybackState(self): 
        return self._playbackState
    
    def getControlsLockout(self): 
        return self._lockout
    
    def getStartStopStatus(self):
        return self._startStopStatus
    
    def setStartStopStatus(self, status):
        self._startStopStatus = status

    def setLockout(self, l): 
        self._lockout = l

    def getLockout(self): 
        return self._lockout
    
    def interlocksActive(self):
        if(self._playbackInterlock or self._lampInterlock or self._serverInterlock or self._lockout):
            return True
        else: 
            return False
    
    def start(self):
        thread = threading.Thread(target=self.run, args=[])
        thread.start()

    # main
    def run(self):
        # loop
        while(True):
            try: 
                # init vars to detect for change
                tlampInterlock = self._lampInterlock
                tserverInterlock = self._serverInterlock
                tplaybackInterlock = self._playbackInterlock

                self._projectorOnline = self.projector.isOnline()
                self._projectorPower = self.projector.getPower()
                self._serverOnline = self.dolby.isOnline()
                self._serverBooted = self.dolby.getBooted()
                # print(" *************************************** ")
                # print("Projector online: " + str(self._projectorOnline))
                # print("Projector Power: " + str(self._projectorPower))
                # print("Server Booted: " + str(self._serverBooted))
                # print("Server Online: " + str(self._serverOnline))

                # Playback interlock
                if(self._serverBooted):
                    self._playbackState = self.dolby.getPlaybackState()
                    if(self._playbackState == "Play"):
                        self._playbackInterlock = True
                    else: 
                        self._playbackInterlock = False
                else: 
                    self._playbackInterlock = False
                    self._playbackState = "offline"
                # print(self._playbackState)
                # print("Playback Interlock: " + str(self._playbackInterlock))
                # Lamp & Server interlock
                if(self._projectorOnline == False):
                    self._lampInterlock = False
                    self._serverInterlock = False
                else: 
                    if(self._projectorPower == 1):
                        self._lampInterlock = True
                    else:
                        # Projector will immediately report the power level requested (3 or 0), but if a cooldown is active, we still need 
                        # to keep the lamp interlock active
                        cooldown = self.projector.getCooldown()
                        if(cooldown != 0): 
                            self._lampInterlock = True
                        else: 
                            self._lampInterlock = False

                    if(self._serverBooted):
                        self._serverInterlock = True
                    else: self._serverInterlock = False

                # On-Change update all connected clients
                if(tlampInterlock != self._lampInterlock or tserverInterlock != self._serverInterlock or tplaybackInterlock != self._playbackInterlock):
                    interlocks = self.getInterlocks()
                    msg = { "Number": 2002, "Message": "InterlockMessage", "msg": interlocks}
                    self.MessageBroker.add_message(msg)
                    self.MessageBroker.broadcast()

            except Exception as ex: 
                print(ex)

            time.sleep(10)

class InterlocksDetail: 
    def __init__(self):
        self.id = InterlocksController()

    def __getitem__(self, key):
        if key == "LampInterlock": 
            return self.id.getLampInterlock()
        elif key == "PlaybackInterlock": 
            return self.id.getPlaybackInterlock()
        elif key == "ServerInterlock": 
            return self.id.getServerInterlock()
        elif key == "AVInterlock": 
            return self.id.getAVInterlock()
        elif key == "ControlsLockout": 
            return self.id.getLockout()
        elif key == "ProjectorOnline": 
            return self.id.getProjectorOnline()
        elif key == "ServerOnline": 
            return self.id.getServerOnline()
        elif key == "ServerBooted": 
            return self.id.getServerBooted()
        elif key == "PlaybackState": 
            return self.id.getPlaybackState()
        elif key == "ProjectorPowerLevel": 
            return str(self.id.getProjectorPower())
        else: 
            raise KeyError("{} not found".format(key))