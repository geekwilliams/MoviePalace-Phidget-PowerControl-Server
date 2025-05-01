# This class communicates with designated projector based on auditorium set in Globals
import socket
import Globals
from devices.Device import Device
import traceback

class Projector(Device):
    host = None
    port = 5000  # Solaria api uses this port
 
    def __init__(self):
        super().__init__("10.18.140.{}".format(Globals.auditorium_number + 190))
        self.host = "10.18.140.{}".format(Globals.auditorium_number + 190)
        self.con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # return int power status
    def getPower(self):
        try: 
            con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            con.settimeout(5)
            con.connect((self.host, self.port))
            msg = "(PWR?)\r"
            con.sendall(msg.encode())
            res = b""
            while True:
                chunk = con.recv(1024)
                if ")" in chunk.decode(): 
                    res += chunk
                    break
                res += chunk
            con.close()
            return int((res.decode())[5:8]) # should remove all but int, needs testing int prod
        
        except Exception as e:
            print("Error: Unable to connect to projector at {}".format(self.host))
            traceback.print_exc()

    def powerup(self):
        try: 
            con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            con.settimeout(5)
            con.connect((self.host, self.port))
            msg = "(PWR0)\r"
            con.sendall(msg.encode())
            # res = (self.con.recv(1024)).decode()
            con.close()
        except Exception as e:
            print("Unable to send power-on command to projector at {}".format(self.host))
            print(e)
    
    def standby(self):
        try: 
            con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            con.settimeout(5)
            con.connect((self.host, self.port))
            msg = "(PWR3)\r"
            con.sendall(msg.encode())
            # res = (self.con.recv(1024)).decode()
            con.close()
        except Exception as e:
            print("Unable to send standby command to projector at {}".format(self.host))
            print(e) 
    
    def getCooldown(self):
        try:
            con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            con.settimeout(5)
            con.connect((self.host, self.port))
            msg = ("(PWR+COOL?)\r")
            con.sendall(msg.encode())
            res = b""
            while True:
                chunk = con.recv(1024)
                if ")" in chunk.decode():
                    res += chunk
                    break
                res += chunk
            con.close()
            return int((res.decode())[10:15])
        except Exception as e: 
            print("Unable to get cooldown")
            print(e)

    


