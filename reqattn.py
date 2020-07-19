#!/usr/bin/env python3
# send table key value ...pairs

from time import sleep
import select
import socket
import sys
import os
import logging
import json

class Client:
    sockbuffLen = 1024

    def __init__(self, server_address = os.environ['HOME'] + '/.cache/var/attention-mgr/uds_socket'):
        logging.basicConfig(format='%(message)s')
        self.log            = logging.getLogger(__name__)
        self.server_address = server_address
        self.connect()

    def connect(self):
        # Create a UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.setblocking(False)
        self.socks = [ self.sock ]
        # Connect the socket to the port where the server is listening
        self.log.warning('connecting to %s' % self.server_address)
        for s in self.socks:
            try:
                s.connect(self.server_address)
            except socket.error as msg:
                self.log.warning(msg)
                sys.exit(1)

    def send(self, msg):
        sock = self.sock
        try:
            timeout_in_seconds = 1
            self.log.warning('%s: sending "%s"' % (sock.getsockname(), msg))
            sock.send(msg.encode())

            # https://stackoverflow.com/a/2721734
            readable, writable, exceptional = select.select([sock], [], [], timeout_in_seconds)
            for s in readable:
                data = s.recv( Client.sockbuffLen )
                if data:
                    self.log.warning('%s: received "%s"' % (s.getsockname(), data.decode()))
        finally:
            self.log.warning('closing socket %s' % sock.getsockname())
            sock.close()

def listToDict(lst):
    op = {lst[i]: lst[i + 1] for i in range(0, len(lst), 2)}
    return op


def main():
    client  = Client()
    table   = sys.argv[1]
    keyvals = listToDict( sys.argv[2:] )
    tableKv = dict()

    tableKv[ table ] = keyvals
    jsonstr          = json.dumps( tableKv )

    client.send( json.dumps( tableKv ) )




if __name__=="__main__":
    main()




