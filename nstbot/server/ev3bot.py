import nstbot.server as server

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
        else:
            mode = 'float'
        for index in range(8):
            fn = r'/sys/class/servo-motor/motor%d/command' % index
            with open(fn, 'w') as f:
                f.write(mode)
    

if __name__ == '__main__':
    EV3Server().run()
