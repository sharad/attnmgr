#!/usr/bin/env python3
# send table key value ...pairs


import socket
import sys
import logging
import pickle

class Client:
    sockbuffLen = 1024

    def __init__(self, server_address = './uds_socket'):
        logging.basicConfig(format='%(message)s')
        self.log            = logging.getLogger(__name__)
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

    def send(self, msg):
        try:
            # Send data
            # msg = 'This is the msg.  It will be repeated.'
            byt = msg.encode()

            self.log.warning('sending "%s"' % msg)
            self.sock.sendall(byt)

            amount_received = 0
            amount_expected = len(msg)

            while amount_received < amount_expected:
                data = self.sock.recv( Client.sockbuffLen )
                amount_received += len(data)
                self.log.warning('received "%s"' % data)

        finally:
            self.log.warning('closing socket')
            self.sock.close()



def listToDict(lst):
    op = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return op


def main():
    client  = Client()
    table   = sys.argv[1]
    keyvals = listToDict( sys.argv[2:] )

    # tableKv = dict(table = keyvals)

    print("{}")

    print("{%s: }" % table )

    client.send(( "test" ))




if __name__=="__main__":
    main()
