#!/usr/bin/env python3

import socket
import sys
import os
# https://github.com/Ulauncher/ulauncher-timer/tree/master/timer
import tinydb # https://tinydb.readthedocs.io/en/stable/getting-started.html#basic-usage
# from tinydb import TinyDB, Query
import logging
import json
import rofi


class DaemonBase(object):
    def __init__(self):
        logging.basicConfig(format='%(message)s')
        self.log = logging.getLogger(__name__)

class Database(DaemonBase):
    def __init__(self, dbfile = 'db.json'):
        DaemonBase.__init__(self)
        self.tables = dict();
        self.db     = tinydb.TinyDB(dbfile)

    def add(self, table, json):
        self.db.insert({'type': 'apple', 'count': 7})
        self.db.insert({'type': 'peach', 'count': 3})

        Fruit = tinydb.Query()
        self.db.search(Fruit.type == 'peach')
        self.db.update({'count': 10}, Fruit.type == 'apple')


class Daemon(DaemonBase):
    sockbuffLen = 1024

    def __init__(self, server_address = './uds_socket'):
        DaemonBase.__init__(self)
        self.handlers = dict()
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

    def processHandler(self, hdlrname, js):
        if hdlrname in self.handlers:
            handler = self.handlers[hdlrname]
            handler.run(js)
        else:
            self.log.warning("No handler present for %s" % hdlrname)

    def processJson(self, js):
        if 1 == len(js):
            table = list(js.keys())[0]
            self.processHandler(table, js[table])

    def processConnection(self, connection, client_address):
        try:
            self.log.warning('connection from %s' % client_address)
            msg = ""
            # Receive the data in small chunks and retransmit it
            while True:
                data    = connection.recv( Daemon.sockbuffLen )
                msg += data.decode()
                if data:
                    self.log.warning('sending data back to the client')
                    connection.sendall(data)
                else:
                    self.log.warning('no more data from %s' % client_address)
                    break
        finally:
            # Clean up the connection
            connection.close()
            self.log.warning('received msg = %s' % msg)
            tableKv = json.loads(msg)
            self.processJson(tableKv)

    def loop(self):
        while True:
            # Wait for a connection
            self.log.warning('waiting for a connection')
            connection, client_address = self.sock.accept()
            self.processConnection(connection, client_address)


class Handler(DaemonBase):
    def __init__(self):
        DaemonBase.__init__(self)
        print()

class RemoteSshHandler(Handler):
    def __init__(self):
        Handler.__init__(self)

class XwinSessionHandler(Handler):
    def __init__(self):
        Handler.__init__(self)

    def run(self, json):
        self.log.warning('running client with json = %s' % json)
        self.ask(json)

    def ask(self, json):
        # https://github.com/bcbnz/python-rofi
        r = rofi.Rofi()
        # win = json["winid"]
        prompt = "%s need your attention" % "window"
        options = ["Select it.",
                   "Remind after 10 mins",
                   "Ignore"]
        index, key = r.select(prompt, options)

def main():
    daemon = Daemon()
    daemon.registerHandler("xwin", XwinSessionHandler())
    daemon.loop()



if __name__=="__main__":
    main()

