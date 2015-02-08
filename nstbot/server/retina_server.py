import thread
import socket
import time

import serial

class RetinaServer(object):
    def __init__(self, retina=r'/dev/ttyUSB0', retina_baud=4000000,
                 port=56001):
        self.retina = serial.Serial(retina, baudrate=retina_baud,
                                    rtscts=True, timeout=None)
        thread.start_new_thread(self.retina_reader, ())

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', port))  # allow connections from anywhere
        self.socket.listen(1)              # only allow one connection
        self.conn = None

    def retina_reader(self):
        while True:
            data = self.retina.read(1)
            if self.conn is not None:
                self.conn.sendall(data)
            waiting = self.retina.inWaiting()
            if waiting > 0:
                data = self.retina.read(waiting)
                if self.conn is not None:
                    self.conn.sendall(data)
            time.sleep(0.01)

    def run(self):
        while True:
                print 'waiting for connection'
                self.conn, self.addr = self.socket.accept()

                while True:
                    msg = self.conn.recv(1024)
                    if len(msg) == 0:
                        self.conn = None
                        # client has disconnected
                        break
                    self.retina.write(msg)

if __name__ == '__main__':
    r = RetinaServer()
    r.run()
