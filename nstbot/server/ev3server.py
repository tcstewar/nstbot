import os
import thread
import time
import traceback

import serial

import nstbot.server as server
import nstbot

class Sensor(object):
    def __init__(self, server, port, period):
        self.server = server
        self.port = port
        self.period = period
        self.path = None
        self.running = True
        thread.start_new_thread(self.run, ())

    def run(self):
        while self.running:
            if self.path is None:
                try:
                    self.find_path()
                except IOError:
                    pass
            if self.path is not None:
                value = self.get_value()
                msg = '-LS%d %d' % (self.port, value)
                print 'msg', msg
                try:
                    self.server.send(msg)
                except:
                    traceback.print_exc()
                    self.running = False
            time.sleep(self.period)

    def find_path(self):
        base = r'/sys/class/msensor'
        for path in os.listdir(base):
            with open(os.path.join(base, path, 'port_name')) as f:
                port_name = f.read().strip()
            if port_name == 'in%d' % self.port:
                with open(os.path.join(base, path, 'name')) as f:
                    self.name = f.read().strip()
                self.path = os.path.join(base, path)
                self.fn = os.path.join(self.path, 'value0')
                self.init_sensor()

    def init_sensor(self):
        if self.name == 'lego-nxt-us':
            with open(os.path.join(self.path, 'mode'), 'w') as f:
                f.write('US-DIST-IN')
            with open(os.path.join(self.path, 'poll_ms'), 'w') as f:
                f.write('50')  # fastest polling time possible

    def get_value(self):
        try:
            with open(self.fn) as f:
                value = f.read().strip()
        except IOError:
            self.path = None
            return 0

        value = int(value)
        if self.name == 'lego-nxt-us':
            v_0 = 300.0
            v_1 = 25.0
        elif self.name == 'ev3-uart-33':
            v_0 = 100.0
            v_1 = 5.0
        else:
            print 'unknown sensor type', self.name
            return 0

        v = (value - v_0) / (v_1 - v_0)
        if v < 0:
            v = 0
        if v > 1:
            v = 1
        return int(v * 100)





class EV3Server(server.NSTServer):
    def __init__(self, **kwargs):
        super(EV3Server, self).__init__(**kwargs)
        self.device_path = {}

        self.sensors = {}

    @server.command('!M(\d)=(-?\d+)',
                    '!M[0-7]=[-100 to 100]',
                    'set servo motor position')
    def servo(self, index, setting):
        index = int(index)
        setting = int(setting)
        if setting > 100:
            setting = 100
        if setting < -100:
            setting = -100
        fn = r'/sys/class/servo-motor/motor%d/position' % index
        with open(fn, 'w') as f:
            f.write('%d' % setting)

    def find_tacho_motor(self, port):
        base = r'/sys/class/tacho-motor'
        for path in os.listdir(base):
            with open(os.path.join(base, path, 'port_name')) as f:
                port_name = f.read().strip()
            if port_name == 'out' + port:
                return os.path.join(base, path)
        return None

    @server.command('!M([+-])', '!M+/-', 'enable/disable motors')
    def servo_activate(self, flag):
        if flag == '+':
            mode = 'run'
            mode_t = '1'
        else:
            mode = 'float'
            mode_t = '0'
        for port in 'ABCD':
            path = self.find_tacho_motor(port)
            if path is not None:
                self.device_path[('tacho', port)] = path
                with open(os.path.join(path, 'run'), 'w') as f:
                    f.write(mode_t)
        #for index in range(8):
        #    fn = r'/sys/class/servo-motor/motor%d/command' % index
        #    with open(fn, 'w') as f:
        #        f.write(mode)

    @server.command('!M([ABCD])=(-?\d+)',
                    '!M[A-D]=[-100 to 100]',
                    'set motor speed')
    def motor(self, port, setting):
        setting = int(setting)
        if setting > 100:
            setting = 100
        if setting < -100:
            setting = -100

        fn = self.device_path.get(('tacho', port), None)
        if fn is None:
            fn = self.find_tacho_motor(port)
            self.device_path[('tacho', port)] = fn
            if fn is None:
                return

        try:
            with open(os.path.join(fn, 'duty_cycle_sp'), 'w') as f:
                f.write('%d' % setting)
        except IOError:
            del self.device_path[('tacho', port)]

    @server.command(r'!LS[+]([1234]),(\d+)', '!LS+PORT,PERIOD',
                    'stream sensor data')
    def sensor_activate(self, port, period):
        port = int(port)
        period = int(period) * 0.001
        if port in self.sensors:
            self.sensors[port].running = False
        self.sensors[port] = Sensor(self, port, period)

    @server.command(r'!LS[-]([1234])', '!LS-PORT',
                    'stop streaming sensor data')
    def sensor_deactivate(self, port):
        port = int(port)
        if port in self.sensors:
            self.sensors[port].running = False
            del self.sensors[port]

if __name__ == '__main__':
    ev3 = EV3Server()
    #print ev3.find_tacho_motor('A')
    #print ev3.find_sensor(name='lego-nxt-us', port=3)
    ev3.run()
