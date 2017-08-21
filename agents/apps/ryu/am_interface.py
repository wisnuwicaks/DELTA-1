import socket
from os.path import expanduser
import sys
import struct
import binascii

class AMInterface:
    def __init__(self, obj, logger):
        self.appAgent = obj
        self.logger = logger

    def setServerAddr(self):
        server_address = ('10.0.2.2', 3366) # default ip, port pair for vm
        home = expanduser("~")
        f = open(home + "/agent.cfg", "r")

        while True:
            line = f.readline()
            if not line: break

            if "MANAGER_IP" in line:
               manager_ip = line.split("=")[1].rstrip()
            elif "MANAGER_PORT" in line:
               manager_port = int(line.split("=")[1].rstrip())

        if manager_ip is not None and manager_port is not None:
            server_address = (manager_ip, manager_port)

        return server_address


    def connectServer(self, server_address):

        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening

        if not server_address:
            server_address = ('10.0.2.2', 3366)

        print '[AMInterface] Connecting to %s port %s' % server_address
        sock.connect(server_address)

        try:
            # Send AppAgent Message
            message = 'AppAgent'
            m = '\x00' + '\x08' + message
            self.logger.info("[AMInterface] Handshaking with AgentManager...")
            self.writeUTF(sock, message)

            # Receive OK Message
            data = self.readUTF(sock)
            self.logger.info("[AMInterface] Received from AgentManager: " + data)

            # Receive Code
            while True:
                data = self.readUTF(sock)
                self.logger.info("AgentManager: " + data)
                if "3.1.010" in data:
                    print "AgentManager: Fail"
                elif "3.1.020" in data:
                    self.appAgent.testControlMessageDrop()
                elif "3.1.030" in data:
                    self.appAgent.testInfiniteLoops()
                elif "3.1.040" in data:
                    self.appAgent.testInternalStorageAbuse()
                elif "3.1.060" in data:
                    print "AgentManager: Pass"
                elif "3.1.070" in data:
                    result = self.appAgent.testFlowRuleModification()
                    self.writeUTF(sock, result)
                elif "3.1.080" in data:
                    self.appAgent.testFlowTableClearance()
                elif "3.1.80" in data:
                    if "false" in data:
                        self.appAgent.callFlowTableClearance()
                elif "3.1.090" in data:
                    self.appAgent.testEventListenerUnsubscription()
                elif "3.1.100" in data:
                    print "AgentManager: Pass"
                elif "3.1.110" in data:
                    self.appAgent.testMemoryExhaustion()
                elif "3.1.120" in data:
                    self.appAgent.testCPUExhaustion()
        except:
            e = sys.exc_info()[0]
            self.logger.info("[AMInterface] error: " + str(e))

    # read string of utf format
    def readUTF(self, sock):
        size = struct.unpack("!H", sock.recv(2))[0]
        msg = sock.recv(size)
        return msg

    # write string as utf format
    def writeUTF(self, sock, msg):
        size = len(msg)
        sock.send(struct.pack("!H", size))
        sock.send(msg)

if __name__ == "__main__":
     AMInterface()
