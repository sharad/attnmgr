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
import subprocess
import re
from enum import Enum, unique, auto


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

class Utils(DaemonBase):
    def __init__(self):
        DaemonBase.__init__(self)

    def getActiveWindowId():
        root = subprocess.Popen(['xprop', '-root', '_NET_ACTIVE_WINDOW'], stdout=subprocess.PIPE)
        stdout, stderr = root.communicate()
        m = re.search(b'^_NET_ACTIVE_WINDOW.* ([\w]+)$', stdout)
        if m != None:
            window_id = m.group(1)
            return window_id.decode()
        else:
            return None

    def focusWindId(winId):
        root = subprocess.Popen(['wmctrl', '-i', '-a', str(winId)], stdout=subprocess.PIPE)
        stdout, stderr = root.communicate()
        return True

    def getWinTitle(winId):
        window = subprocess.Popen(['xprop', '-id', str(winId), 'WM_NAME'], stdout=subprocess.PIPE)
        stdout, stderr = window.communicate()
        match = re.match(b"WM_NAME\(\w+\) = (?P<name>.+)$", stdout)
        if match != None:
            return match.group("name").decode()




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

class RemoteSshScreenHandler(Handler):
    def __init__(self):
        Handler.__init__(self)

class XwinSessionHandler(Handler):
    Action = Enum('Action', ['Ignore', 'Select', 'Remind'], start=0)

    def __init__(self):
        Handler.__init__(self)

    def giveFocus(self):
        getActiveWindowId()

    def run(self, json):
        self.log.warning('running client with json = %s' % json)
        winid        = int( json["winid"], 10 )
        activewinid  = int( Utils.getActiveWindowId(), 16 )
        wtitle       = Utils.getWinTitle(winid)
        if winid == activewinid:
            self.log.warning("window %s[%d] already have focus" % (wtitle, winid))
        else:
            self.log.warning("window %s[%d] not have focus" % (wtitle, winid))
            if XwinSessionHandler.Action.Select.value == self.ask(json):
                Utils.focusWindId(winid)
            # self.ask(json)
        return True

    def ask(self, json):
        # https://github.com/bcbnz/python-rofi
        r = rofi.Rofi()
        prompt = "%s need your attention" % "window"
        actions = dict()
        actions[XwinSessionHandler.Action.Ignore] = "Ignore"
        actions[XwinSessionHandler.Action.Select] = "Select it."
        actions[XwinSessionHandler.Action.Remind] = "Remind after 10 mins"
        options = actions.values()
        index, key = r.select(prompt, options)
        self.log.warning("index %d, key %d" % (index, key))
        return index

def main():
    daemon = Daemon()
    daemon.registerHandler("xwin", XwinSessionHandler())
    daemon.registerHandler("rsshscreen", RemoteSshScreenHandler())
    daemon.loop()



if __name__=="__main__":
    main()

