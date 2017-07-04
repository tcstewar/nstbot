import thread
import socket
import sys
import time
import timeit

import serial
import numpy as np

class RetinaServer(object):
    def __init__(self, filename, port=56000, packet_size=6, rate=1.0):
        with file(filename, 'rb') as f:
            data = f.read()
            data = np.fromstring(data, np.uint8)

        t = data[2::packet_size].astype(np.uint32)
        t = (t << 8) + data[3::packet_size]
        if packet_size >= 5:
            t = (t << 8) + data[4::packet_size]
        if packet_size >=6:
            t = (t << 8) + data[5::packet_size]

        self.rate = rate

        min_t = t[0]
        max_t = t[-1]
        self.times = t
        self.data = data

        self.offset = min_t
        self.packet_size = packet_size

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', port))  # allow connections from anywhere
        self.socket.listen(1)              # only allow one connection
        self.conn = None

    def run(self):
        while True:
            print 'waiting for connection'
            self.conn, self.addr = self.socket.accept()
            start_time = timeit.default_timer()
            last_index = 0
            packet_size = self.packet_size

            while True:
                #msg = self.conn.recv(1024)
                #if len(msg) == 0:
                #    self.conn = None
                #    # client has disconnected
                #    break
                now = timeit.default_timer()
                dt = (now - start_time)*1000000*self.rate + self.offset

                index = np.argmax(self.times>dt)
                if index > last_index:
                    self.conn.send(self.data[last_index*packet_size:
                                                index*packet_size])
                    last_index = index
                    print(index)
                time.sleep(0.001)

if __name__ == '__main__':
    r = RetinaServer(sys.argv[1], rate=0.1)
    r.run()
