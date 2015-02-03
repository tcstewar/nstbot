import nstbot.server as server
import nstbot

class RetinaProxy(nstbot.RetinaBot):
    def __init__(self, server):
        super(RetinaProxy, self).__init__()
        self.server = server
    def process_retina(self, data):
        self.server.conn.sendall(data)
	print 'retina', len(data)


class EV3Server(server.NSTServer):
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

    @server.command('!M([+-])', '!M+/-', 'enable/disable motors')
    def servo_activate(self, flag):
        if flag == '+':
            mode = 'run'
            mode_t = '1'
        else:
            mode = 'float'
            mode_t = '0'
        for index in range(4):
            fn = r'/sys/class/tacho-motor/motor%d/run' % index
            with open(fn, 'w') as f:
                f.write(mode_t)
        #for index in range(8):
        #    fn = r'/sys/class/servo-motor/motor%d/command' % index
        #    with open(fn, 'w') as f:
        #        f.write(mode)

    @server.command('!M([ABCD])=(-?\d+)', 
                    '!M[A-D]=[-100 to 100]',
                    'set motor speed')
    def motor(self, index, setting):
        index = 'ABCD'.find(index)
        setting = int(setting)
        if setting > 100: 
            setting = 100
        if setting < -100:
            setting = -100
        fn = r'/sys/class/tacho-motor/motor%d/duty_cycle_sp' % index
        with open(fn, 'w') as f:
            f.write('%d' % setting)

    retina_active = False
    def activate_retina(self, port='/dev/ttyUSB0', baud=4000000):
        assert self.retina_active == False
        self.retina = RetinaProxy(self)
        self.retina.connect(nstbot.connection.Serial(port, baud=baud))
        self.retina_active = True

    @server.command('E([+-])', 'E+/-', 'enable/disable retina')
    def retina_setting(self, flag):
        if flag == '+':
            if not self.retina_active:
                self.activate_retina()
            self.retina.retina(True)
        else:
            if not self.retina_active:
                self.activate_retina()
            self.retina.retina(True)

if __name__ == '__main__':
    EV3Server().run()
