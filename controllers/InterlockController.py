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
    _avInterlock = False
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

                # Playback interlock
                if(self._serverBooted):
                    self._playbackState = self.dolby.getPlaybackState()
                    if(self._playbackState == "play"):
                        self._playbackInterlock = True
                    else: 
                        self._playbackInterlock = False
                else: 
                    self._playbackInterlock = False
                    self._playbackState = "offline"

                # Lamp & Server interlock
                if(self._projectorOnline == False):
                    self._lampInterlock = False
                    self._serverInterlock = False
                else: 
                    if(self._projectorPower == 1):
                        self._lampInterlock = True
                    else: self._lampInterlock = False

                    if(self._serverBooted):
                        self._serverInterlock = True
                    else: self._serverInterlock = False

                # On-Change update all connected clients
                if(tlampInterlock != self._lampInterlock or tserverInterlock != self._serverInterlock or tplaybackInterlock != self._playbackInterlock):
                    interlocks = self.getInterlocks()
                    msg = { "Number": 2002, "Message": "InterlockMessage", "msg": interlocks}
                    MessageBroker.add_message(msg)
                    MessageBroker.broadcast()

            except Exception as ex: 
                print(ex)

            time.sleep(10)

class InterlocksDetail: 
    def __init__(self):
        self.id = InterlocksController()

    def __getitem__(self, key):
        if key == "LampInterlock": 
            return self.id._lampInterlock
        elif key == "PlaybackInterlock": 
            return self.id._playbackInterlock
        elif key == "ServerInterlock": 
            return self.id._serverInterlock
        elif key == "AVInterlock": 
            return self.id._avInterlock
        elif key == "ControlsLockout": 
            return self.id._lockout
        elif key == "ProjectorOnline": 
            return self.id._projectorOnline
        elif key == "ServerOnline": 
            return self.id._serverOnline
        elif key == "ServerBooted": 
            return self.id._serverBooted
        elif key == "PlaybackState": 
            return self.id._playbackState
        elif key == "ProjectorPowerLevel": 
            return str(self.id._projectorPower)
        else: 
            raise KeyError("{} not found".format(key))