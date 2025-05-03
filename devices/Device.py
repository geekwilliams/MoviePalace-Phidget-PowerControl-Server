import os

class Device: 
    def __init__(self, host):
        self.host = host
        
    def isOnline(self):
        r = os.system("ping -c 1 -w 1 {} > /dev/null 2>&1".format(self.host))
        if r == 0:
            return True
        else:
            return False