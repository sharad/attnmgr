#!/usr/bin/env python3

import socket
import sys
import os
# https://github.com/Ulauncher/ulauncher-timer/tree/master/timer
import tinydb # https://tinydb.readthedocs.io/en/stable/getting-started.html#basic-usage
# from tinydb import TinyDB, Query
import logging




class Database:
    def __init__(self, dbfile = 'db.json'):
        self.tables = dict();
        self.db     = tinydb.TinyDB(dbfile)

    def add(self, table, json):
        self.db.insert({'type': 'apple', 'count': 7})
        self.db.insert({'type': 'peach', 'count': 3})

        Fruit = tinydb.Query()
        self.db.search(Fruit.type == 'peach')
        self.db.update({'count': 10}, Fruit.type == 'apple')


class Daemon:
    sockbuffLen = 1024

    def __init__(self, server_address = './uds_socket'):
        logging.basicConfig(format='%(message)s')
        self.log = logging.getLogger(__name__)
        self.server_address = server_address
        self.mksocket()

    def mksocket(self):
        # Make sure the socket does not already exist
        try:
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise

        # Create a UDS socket
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        # Bind the socket to the port
        self.log.warning('starting up on %s' % self.server_address)
        self.sock.bind(self.server_address)

        # Listen for incoming connections
        self.sock.listen(1)


    def process(self, connection, client_address):
        try:
            self.log.warning('connection from %s' % client_address)

            # Receive the data in small chunks and retransmit it
            while True:
                data    = connection.recv( Daemon.sockbuffLen )
                message = data.decode()
                # self.log.warning('received "%s"' % message)
                if data:
                    self.log.warning('sending data back to the client')
                    connection.sendall(data)
                else:
                    self.log.warning('no more data from %s' % client_address)
                    break

        finally:
            # Clean up the connection
            connection.close()


    def loop(self):
        while True:
            # Wait for a connection
            self.log.warning('waiting for a connection')
            connection, client_address = self.sock.accept()
            self.process(connection, client_address)


class Handler:
    def __init__(self):
        print()

class RemoteSshHandler(Handler):
    def __init__(self):
        print()

class XwinSessionHandler(Handler):
    def __init__(self):
        print()



def main():
    daemon = Daemon()
    daemon.loop()



if __name__=="__main__":
    main()

