import os
import thread

import nstbot.server as server
import nstbot


class EV3Server(server.NSTServer):
    def __init__(self, retina=r'/dev/ttyUSB0', retina_baud=4000000, **kwargs):
        super(EV3Server, self).__init__(**kwargs)
        self.device_path = {}
        if os.path.exists(retina):
            self.retina = nstbot.connection.Serial(retina, baud=retina_baud)
            thread.start_new_thread(self.retina_passthrough, ())

    def retina_passthrough(self):
        while not self.finished:
            data = self.retina.receive()
            if len(data) > 0 and self.conn is not None:
                self.conn.sendall(data)

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

    @server.command('E([+-])', 'E+/-', 'enable/disable retina')
    def retina_setting(self, flag):
        if self.retina is not None:
            self.retina.send('\nE%s\n' % flag)

    @server.command('!E([01234])', '!E#', 'event data format')
    def retina_data_format(self, value):
        if self.retina is not None:
            self.retina.send('\n!E%s\n' % value)


if __name__ == '__main__':
    ev3 = EV3Server()
    #print ev3.find_tacho_motor('A')
    ev3.run()
