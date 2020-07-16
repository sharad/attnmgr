#!/usr/bin/env python3

import socket
import sys
import logging

class Client:
    def __init__(self, server_address = './uds_socket'):
        logging.basicConfig(format='%(message)s')
        self.log = logging.getLogger(__name__)
        self.server_address = server_address
        self.connect()

    def connect(self):
        # Create a UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        self.log.warning('connecting to %s' % self.server_address)
        try:
            self.sock.connect(self.server_address)
        except socket.error as msg:
            self.log.warning(msg)
            sys.exit(1)

    def send(self):
        try:
            # Send data
            message = 'This is the message.  It will be repeated.'
            byt     = message.encode()
            self.log.warning('sending "%s"' % message)
            self.sock.sendall(byt)

            amount_received = 0
            amount_expected = len(message)

            while amount_received < amount_expected:
                data = self.sock.recv(16)
                amount_received += len(data)
                self.log.warning('received "%s"' % data)

        finally:
            self.log.warning('closing socket')
            self.sock.close()




def main():
    client = Client()
    client.send()



if __name__=="__main__":
    main()
