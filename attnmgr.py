#!/usr/bin/env python3

# https://pymotw.com/2/select/

import socket
import select
import errno
from time import sleep
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
import queue
import threading
from enum import Enum, unique, auto


# ##### example #####
# import threading, queue

# q = queue.Queue()

# def worker():
#     while True:
#         item = q.get()
#         print(f'Working on {item}')
#         print(f'Finished {item}')
#         q.task_done()

# # turn-on the worker thread
# threading.Thread(target=worker, daemon=True).start()

# # send thirty task requests to the worker
# for item in range(30):
#     q.put(item)
# print('All task requests sent\n', end='')

# # block until all tasks are done
# q.join()
# print('All work completed')
# ##### example #####

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

class Worker(threading.Thread, DaemonBase):
    # https://pymotw.com/2/threading/
    # https://realpython.com/intro-to-python-threading/
    def __init__(self,
                 group=None,
                 target=None,
                 name=None,
                 args=(),
                 kwargs=None,
                 verbose=None):
        DaemonBase.__init__(self)
        threading.Thread.__init__(self,
                                  group=group,
                                  target=target,
                                  name=name) # , verbose=verbose
        self.args   = args
        self.kwargs = kwargs
        self.handler = kwargs['handler']
        self.q      = queue.Queue()
        self.start()
        return

    def put(self, msg):
        self.q.put(msg)

    def get(self):
        return self.q.get()

    def done(self):
        return self.q.task_done()

    def run(self):
        logging.debug('running with %s and %s', self.args, self.kwargs)
        logging.warning('running with %s and %s', self.args, self.kwargs)
        while True:
            item     = self.get()
            print(f'Working on {item}')
            js       = item['js']
            daemon   = item['daemon']
            sock     = item['sock']
            peername = sock.getpeername()
            response = self.handler.run(js)
            self.log.warning('response "%s" to %s' % (response, peername))
            daemon.message_queues[sock].put(response)
            print(f'Finished {item}')
            self.done()

class Daemon(DaemonBase):
    sockbuffLen = 1024

    def __init__(self, server_address = os.environ['HOME'] + '/.cache/var/attention-mgr/uds_socket'):
        DaemonBase.__init__(self)
        # self.handlers = {}
        self.message_queues = {}
        self.message_js = {}
        self.server_address = server_address
        self.mksocket()
        self.workers = {}

    def mksocket(self):
        # Make sure the socket does not already exist
        try:
            os.makedirs( os.path.dirname( self.server_address ), exist_ok = True )
            os.unlink(self.server_address)
        except OSError:
            if os.path.exists(self.server_address):
                raise
        # Create a UDS socket
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(0)
        # Bind the socket to the port
        self.log.warning('starting up on %s' % self.server_address)
        sock.bind(self.server_address)

        # Listen for incoming connections
        sock.listen(5)

        self.servers = [ sock ]
        self.inputs  = [ sock ]
        self.outputs = [  ]

    def registerHandler(self, hdlrname, handler):
        # self.handlers[hdlrname] = handler
        self.workers[hdlrname] = Worker(kwargs = {'handler': handler})

    def processHandler(self, hdlrname, js, sock):
        if hdlrname in self.workers:
            self.workers[hdlrname].put({'js': js, 'daemon': self, 'sock': sock})
        else:
            self.log.warning("No handler present for %s" % hdlrname)

    def processJson(self, js, sock):
        if 1 == len(js):
            table = list(js.keys())[0]
            self.processHandler(table, js[table], sock)
            return "ok"

    def is_json(self, myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    def processConnection(self, s, client_address):
        self.log.warning('existing connection from %s' % client_address)
        data = s.recv( Daemon.sockbuffLen )
        if data:
            # A readable client socket has data
            self.log.warning('received "%s" from %s' % (data, s.getpeername()))
            if s in self.message_js:
                self.message_js[s] += data.decode()
            else:
                self.message_js[s] = data.decode()

            if self.is_json( self.message_js[s] ):
                tableKv  = json.loads( self.message_js[s] )
                response = self.processJson(tableKv, s) # send in thread
                if s not in self.outputs:
                    self.outputs.append(s)
            else:
                self.message_queues[s].put("not processed")
                # Add output channel for response
                if s not in self.outputs:
                    self.outputs.append(s)
        else:
            # Interpret empty result as closed connection
            self.log.warning('closing %s after reading no data' % client_address)
            # Stop listening for input on the connection
            if s in self.outputs:
                self.outputs.remove(s)
            self.inputs.remove(s)
            s.close()
            # Remove message queue
            del self.message_queues[s]


    def loop(self):
        # https://pymotw.com/2/select/
        while self.inputs:
            # Wait for at least one of the sockets to be ready for processing
            self.log.warning('\nwaiting for the next event')
            readable, writable, exceptional = select.select(self.inputs, self.outputs, self.inputs, 1)
            for s in readable:
                self.log.warning('loop for s=%s', s)
                if s in self.servers:
                    # A "readable" server socket is ready to accept a connection
                    connection, client_address = s.accept()
                    self.log.warning('new connection from %s' % client_address)
                    connection.setblocking(0)
                    self.inputs.append(connection)
                    # Give the connection a queue for data we want to send
                    self.message_queues[connection] = queue.Queue()
                else:
                    self.processConnection(s, client_address)

            for s in writable:
                try:
                    next_msg = self.message_queues[s].get_nowait()
                except queue.Empty:
                    # No messages waiting so stop checking for writability.
                    self.log.warning('output queue for %s is empty' % s.getpeername())
                    self.outputs.remove(s)
                else:
                    self.log.warning('sending "%s" to %s' % (next_msg, s.getpeername()))
                    s.send(next_msg.encode())

            for s in exceptional:
                self.log.warning('handling exceptional condition for %s' % s.getpeername())
                # Stop listening for input on the connection
                self.inputs.remove(s)
                if s in self.outputs:
                    self.outputs.remove(s)
                s.close()
                del self.message_queues[s]


class Handler(DaemonBase):
    def __init__(self):
        DaemonBase.__init__(self)
        print()

class RemoteSshScreenHandler(Handler):
    def __init__(self):
        Handler.__init__(self)
    def run(self):
        self.add(json)

class XwinSessionHandler(Handler):
    Action = Enum('Action', ['Ignore', 'Select', 'Remind'], start=0)

    def __init__(self):
        Handler.__init__(self)

    def defaultJson(self):
        return {'cmd': "nocli",
                'winid': "0",
                'timetaken': 0}

    def ask(self, json):
        # https://github.com/bcbnz/python-rofi
        r = rofi.Rofi()
        winid    = int( json["winid"], 10 )
        wtitle   = Utils.getWinTitle(winid)
        wtitleId = "%s[%d]" % (wtitle, winid)
        prompt   = "%s need your attention" % wtitleId
        actions  = dict()

        message = "Finished %s" % json['cmd']
        actions[XwinSessionHandler.Action.Ignore] = "Ignore %s" % wtitleId
        actions[XwinSessionHandler.Action.Select] = "Select %s" % wtitleId
        actions[XwinSessionHandler.Action.Remind] = "Remind after 10 mins"
        options = actions.values()
        index, key = r.select(prompt, options, message )
        self.log.warning("index %d, key %d" % (index, key))
        return index

    def giveFocus(self, winid):
        Utils.focusWindId(winid)

    def run(self, json):
        default =  self.defaultJson();
        default.update( json )
        json    = default
        self.log.warning('running client with json = %s' % json)
        winid        = int( json["winid"], 10 )
        activewinid  = int( Utils.getActiveWindowId(), 16 )
        wtitle       = Utils.getWinTitle(winid)
        if winid == activewinid:
            self.log.warning("window %s[%d] already have focus" % (wtitle, winid))
        else:
            self.log.warning("window %s[%d] not have focus" % (wtitle, winid))
            if XwinSessionHandler.Action.Select.value == self.ask(json):
                self.giveFocus(winid)
        return True

def main():
    daemon = Daemon()
    daemon.registerHandler("xwin", XwinSessionHandler())
    daemon.registerHandler("rsshscreen", RemoteSshScreenHandler())
    daemon.loop()



if __name__=="__main__":
    main()

