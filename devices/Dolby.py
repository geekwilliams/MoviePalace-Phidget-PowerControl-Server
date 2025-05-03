# This class confirms if server is online and booted
import os
from devices.Device import Device
import Globals
import socket
import json
import traceback

class Dolby(Device): 
    host = None
    port = 80
    sessionID = None

    def __init__(self):
        super().__init__("10.18.140.{}".format(Globals.auditorium_number + 110))
        self.host = "10.18.140.{}".format(Globals.auditorium_number + 110)


    def login(self):
        try:
            loginSoapRequest = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v1=\"http://www.doremilabs.com/dc/dcp/json/v1_0\"><soapenv:Header/><soapenv:Body>><v1:Login><username>manager</username><password>password</password></v1:Login></soapenv:Bodyy></soapenv:Envelope>"
            path = "http://" + self.host + "/dc/dcp/json/v1/SessionManagement"
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cs.settimeout(2)
            cs.connect((self.host, 80))
            message = ("POST {} HTTP/1.1\r\n" +
                                "Host: {}\r\n" + 
                                "Content-Type: application/x-www-form-urlencoded\r\n" +
                                "Content-Length: {}\r\n" +
                                "Connection: close\r\n\r\n" + # extra \r\n adds empty line and indicates the end of the headers
                                "{}").format(path, self.host, len(loginSoapRequest), loginSoapRequest) #The body of the request
            cs.sendall(message.encode())
            response = b""
            while True: 
                chunk = cs.recv(1024)
                if not chunk:
                    break
                response += chunk
            
            body = (response.decode()).split("\r\n\r\n")[1]
            self.sessionID = json.loads(body)["LoginResponse"]["sessionId"]
            cs.close()
            # return

        except Exception as ex: 
            print("Error communicating with server")
            traceback.print_exc()


    def logout(self):
        if self.sessionID != None: 
            try:
                loginSoapRequest = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v1=\"http://www.doremilabs.com/dc/dcp/json/v1_0\"><soapenv:Header/><soapenv:Body><v1:Logout><sessionId>{}</sessionId></v1:Logout></soapenv:Bodyy></soapenv:Envelope>".format(self.sessionID)
                path = "http://" + self.host + "/dc/dcp/json/v1/SessionManagement"
                cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cs.settimeout(2)
                cs.connect((self.host, 80))
                message = ("POST {} HTTP/1.1\r\n" +
                                    "Host: {}\r\n" + 
                                    "Content-Type: application/x-www-form-urlencoded\r\n" +
                                    "Content-Length: {}\r\n" +
                                    "Connection: close\r\n\r\n" + # extra \r\n adds empty line and indicates the end of the headers
                                    "{}").format(path, self.host, len(loginSoapRequest), loginSoapRequest) #The body of the request
                cs.sendall(message.encode())
                # res = json.loads(cs.recv(1024).decode())
                # self.sessionID = res["LoginResponse"]["sessionId"]
                cs.close()
                # return

            except Exception as ex: 
                print("Error communicating with server")
                print(ex)
                

    def getBooted(self):
        try: 
            endpoint = "/dc/dcp/json/v1/WebUI"
            soaprequest = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v1=\"http://www.doremilabs.com/dc/dcp/json/v1_0\"><soapenv:Header/><soapenv:Body>><v1:GetConnectionCount></v1:GetConnectionCount>></soapenv:Bodyy></soapenv:Envelope>"
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cs.settimeout(2)
            cs.connect((self.host, 80))
            message = ("POST {} HTTP/1.1\r\n" +
                                "Host: {}\r\n" + 
                                "Content-Type: application/x-www-form-urlencoded\r\n" +
                                "Content-Length: {}\r\n" +
                                "Connection: close\r\n\r\n" + # extra \r\n adds empty line and indicates the end of the headers
                                "{}").format(endpoint, self.host, len(soaprequest), soaprequest) #The body of the request
            cs.sendall(message.encode())
            response = b""
            while True: 
                chunk = cs.recv(1024)
                if not chunk:
                    break
                response += chunk
            headers = ((response.decode()).split("\r\n\r\n"))[0]
            sub = headers.split(" ")
            code = int(sub[1])
            if code == 200:
                return True
            else:
                return False
        except Exception as ex:
            return False
        
    
    def getPlaybackState(self):
        self.login()

        try:
            getSystemStatusRequest = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v1=\"http://www.doremilabs.com/dc/dcp/json/v1_0\"><soapenv:Header/><soapenv:Body><v1:GetSystemOverview><sessionId>{}</sessionId></v1:GetSystemOverview></soapenv:Body></soapenv:Envelope>".format(self.sessionID)
            endpoint = "http://" + self.host + "/dc/dcp/json/v1/SystemOverview"
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cs.settimeout(2)
            cs.connect((self.host, 80))
            message = ("POST {} HTTP/1.1\r\n" +
                        "Host: {}\r\n" + 
                        "Content-Type: application/x-www-form-urlencoded\r\n" +
                        "Content-Length: {}\r\n" +
                        "Connection: close\r\n\r\n" + # extra \r\n adds empty line and indicates the end of the headers
                        "{}").format(endpoint, self.host, len(getSystemStatusRequest), getSystemStatusRequest) #The body of the request
            cs.sendall(message.encode())
            response = b""
            while True: 
                chunk = cs.recv(1024)
                if not chunk:
                    break
                response += chunk
            
            body = (response.decode()).split("\r\n\r\n")[1]
            cs.close()
            self.logout()
            return json.loads(body)["GetSystemOverviewResponse"]["playback"]["stateInfo"]

        except Exception as ex:
            print(ex)
            return "unknown"
        
        
    def shutdown(self):
        if self.sessionID == None: 
            self.login()

        try: 
            endpoint = "http://" + self.host + "/dc/dcp/json/v1/PowerManagement"
            shutdownRequest = ("<SOAP-ENV:Envelope xmlns:SOAP-ENV=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:ns1=\"http://www.doremilabs.com/dc/dcp/json/v1_0\">" + 
                                        "<soap-env:Body>" + 
                                        "<ns1:Shutdown>" +
                                        "<sessionId>" + self.sessionID + "</sessionId>"+
                                        "<delayMinutes>0</delayMinutes>" + 
                                        "</ns1:Shutdown>" +
                                        "</soap-env:Body>" +
                                        "</soap-env:Envelope>")
            cs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cs.settimeout(2)
            cs.connect((self.host, 80))
            message = ("POST {} HTTP/1.1\r\n" +
                        "Host: {}\r\n" + 
                        "Content-Type: application/x-www-form-urlencoded\r\n" +
                        "Content-Length: {}\r\n" +
                        "Connection: close\r\n\r\n" + # extra \r\n adds empty line and indicates the end of the headers
                        "{}").format(endpoint, self.host, len(shutdownRequest), shutdownRequest) #The body of the request
            cs.sendall(message.encode())
            cs.close()
        
        except Exception as ex: 
            print(ex)




    
