import os
import thread
import time

import serial

import nstbot.server as server
import nstbot

class Sensor(object):
    def __init__(self, server, path, period, prefix):
        self.server = server
        self.path = path
        self.period = period
        self.prefix = prefix
        self.init()
        self.running = True
        thread.start_new_thread(self.run, ())
    def run(self):
        while self.running:
            value = self.get_value()
            try:
                self.server.send('\n%s %s' % (self.prefix, value))
            except:
                print 'Lost sensor connection'
                return
            time.sleep(self.period)

class Ultrasonic(Sensor):
    def init(self):
        with open(os.path.join(self.path, 'mode'), 'w') as f:
            f.write('US-DIST-IN')
        with open(os.path.join(self.path, 'poll_ms'), 'w') as f:
            f.write('50')  # fastest polling time possible
        self.fn = os.path.join(self.path, 'value0')

    def get_value(self):
        with open(self.fn) as f:
            return f.read().strip()

class EV3Server(server.NSTServer):
    def __init__(self, retina=r'/dev/ttyUSB0', retina_baud=4000000, **kwargs):
        super(EV3Server, self).__init__(**kwargs)
        self.device_path = {}

        if os.path.exists(retina):
            self.retina = serial.Serial(retina, baudrate=retina_baud,
                                        rtscts=True, timeout=None)
            thread.start_new_thread(self.retina_passthrough, ())
        else:
            self.retina = None

        self.sensors = {}

    def retina_passthrough(self):
        while not self.finished:
            waiting = self.retina.inWaiting()
            if waiting > 0:
                data = self.retina.read(waiting)
                if self.conn is not None:
                    try:
                        self.conn.sendall(data)
                    except Exception:
                        pass
            else:
                time.sleep(0.001)

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

    def find_sensor(self, name, port):
        base = r'/sys/class/msensor'
        for path in os.listdir(base):
            with open(os.path.join(base, path, 'name')) as f:
                n = f.read().strip()
            if n != name:
                continue
            with open(os.path.join(base, path, 'port_name')) as f:
                port_name = f.read().strip()
            if port_name == 'in%d' % port:
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

    @server.command('E([+-])', 'E+/-', 'enable/disable retina')
    def retina_setting(self, flag):
        if self.retina is not None:
            self.retina.write('\nE%s\n' % flag)

    @server.command('!E([01234])', '!E#', 'event data format')
    def retina_data_format(self, value):
        if self.retina is not None:
            self.retina.write('\n!E%s\n' % value)

    @server.command(r'!LS[+]([1234]),(.+),(\d+)', '!LS+PORT,SENSOR,PERIOD',
                    'stream sensor data')
    def sensor_activate(self, port, sensor, period):
        port = int(port)
        period = int(period) * 0.001
        if sensor == 'US':
            name = 'lego-nxt-us'
            cls = Ultrasonic
        else:
            print 'unknown sensor', sensor
            return
        path = self.find_sensor(name, port)
        if path is None:
            print 'no attached sensor', sensor, name, port
            return
        key = sensor, port
        if key in self.sensors:
            self.sensor_deactivate(port, sensor)
        prefix = '-LS%s%d' % (sensor, port)
        self.sensors[key] = cls(self, path, period, prefix)


    @server.command(r'!LS[-]([1234]),(.+)', '!LS-PORT,SENSOR',
                    'stop streaming sensor data')
    def sensor_deactivate(self, port, sensor):
        port = int(port)
        key = sensor, port
        if key in self.sensors:
            self.sensors[key].running = False
            self.sensors[key] = None

if __name__ == '__main__':
    ev3 = EV3Server()
    #print ev3.find_tacho_motor('A')
    #print ev3.find_sensor(name='lego-nxt-us', port=3)
    ev3.run()
