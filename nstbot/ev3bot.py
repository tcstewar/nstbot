import nstbot
import retinabot

class EV3Bot(retinabot.RetinaBot):
    def initialize(self):
        super(EV3Bot, self).initialize()
        self.ultrasonic = {1: 0, 2: 0, 3: 0, 4: 0}
        self.connection.send('!M+\n')
    def disconnect(self):
        self.connection.send('!M-\n')
        super(EV3Bot, self).disconnect()

    def servo(self, index, position, msg_period=None):
        position = int(position * 100)
        if position < -100:
            position = -100
        if position > 100:
            position = 100
        cmd = '!M%d=%d\n' % (index, position)
        self.send('servo%d' % index, cmd, msg_period=msg_period)

    def motor(self, index, power, msg_period=None):
        power = int(power * 100)
        if power < -100:
            power = -100
        if power > 100:
            power = 100
        cmd = '!M%s=%d\n' % ('ABCD'[index], power)
        self.send('motor%d' % index, cmd, msg_period=msg_period)

    def activate_sensor(self, name, ports, period=0.05):
        if name == 'ultrasonic':
            code = 'US'
        else:
            raise Exception('unknown sensor: %s' % name)

        period_ms = int(period * 1000)

        for port in ports:
            cmd = '!LS+%d,%s,%d\n' % (port, code, period_ms)
            self.send('', cmd, msg_period=None)

    def process_ascii(self, msg):
        #print 'ascii', `msg`
        if msg.startswith('-LSUS'):
            port = int(msg[5])
            value = int(msg[7:])
            max = 100
            if value > 100:
                value = 100
            self.ultrasonic[port] = value / float(max)
        elif len(msg) == 0:
            pass
        else:
            print 'unknown msg', `msg`

if __name__ == '__main__':
    import time

    import connection
    bot = EV3Bot()
    bot.connect(connection.Socket('192.168.1.161'))
    #bot.connect(connection.Socket('10.162.177.187'))
    time.sleep(1)
    bot.retina(True, bytes_in_timestamp=0)
    bot.show_image()

    bot.activate_sensor('ultrasonic', [1, 2, 3, 4])


    import random
    while True:
        time.sleep(0.1)
        print [bot.ultrasonic[x] for x in [1, 2, 3, 4]]
        bot.motor(0, 0)
        bot.motor(1, 0)
        bot.motor(2, 0)
        #bot.retina(True)
        #bot.servo(0, random.uniform(-1, 1))
