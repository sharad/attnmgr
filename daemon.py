#!/usr/bin/env python3

import socket
import sys
import os
# https://github.com/Ulauncher/ulauncher-timer/tree/master/timer
import tinydb # https://tinydb.readthedocs.io/en/stable/getting-started.html#basic-usage
# from tinydb import TinyDB, Query
import logging
import json




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

    def registerHandler(self, hdlrname, handler):
        self.handlers[hdlrname] = handler

    def processHandler(self, hdlrname, json):
        if self.handlers[hdlrname]:
            handler = self.handlers[hdlrname](json)
            handler.run()

    def processJson(self, json):
        if 1 == len(json):
            table = list(json.keys())[0]
            self.processHandler(self.tableHandler[table], json[table])

    def processConnection(self, connection, client_address):
        try:
            self.log.warning('connection from %s' % client_address)
            msg = ""
            # Receive the data in small chunks and retransmit it
            while True:
                data    = connection.recv( Daemon.sockbuffLen )
                msg += data.decode()
                # self.log.warning('received "%s"' % msg)
                if data:
                    self.log.warning('sending data back to the client')
                    connection.sendall(data)
                else:
                    self.log.warning('no more data from %s' % client_address)
                    break
        finally:
            # Clean up the connection
            connection.close()
            tableKv = json.load(msg)
            self.processJson(tableKv)

    def loop(self):
        while True:
            # Wait for a connection
            self.log.warning('waiting for a connection')
            connection, client_address = self.sock.accept()
            self.processConnection(connection, client_address)


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

