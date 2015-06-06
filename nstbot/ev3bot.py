import threading

from . import nstbot

class EV3Bot(nstbot.NSTBot):
    def initialize(self):
        super(EV3Bot, self).initialize()
        self.lego_sensors = [0, 0, 0, 0]
        self.connection.send('!M+\n')

    def connect(self, connection):
        super(EV3Bot, self).connect(connection)
        thread = threading.Thread(target=self.sensor_loop)
        thread.start()

    def disconnect(self):
        self.connection.send('!M-\n')
        super(EV3Bot, self).disconnect()

    def sensor_loop(self):
        """Handle all data coming from the robot."""
        buffered_ascii = ''
        while True:
            data = self.connection.receive()

            buffered_ascii += data

            while '\n' in buffered_ascii:
                cmd, buffered_ascii = buffered_ascii.split('\n', 1)
                self.process_ascii(cmd)


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

    def motors(self, powers, msg_period=None):
        p = []
        for i, pp in enumerate(powers):
            pp = int(pp * 100)
            if pp < -100:
                pp = -100
            if pp > 100:
                pp = 100
            p.append(pp)
        cmd = '!T %d %d %d %d\n' % tuple(p)
        self.send('motors', cmd, msg_period=msg_period)

    def activate_sensor(self, ports, period=0.05):
        period_ms = int(period * 1000)

        for port in ports:
            cmd = '!LS+%d,%d\n' % (port, period_ms)
            self.send('', cmd, msg_period=None)

    def process_ascii(self, msg):
        if msg.startswith('-LS'):
            port = int(msg[3])
            value = int(msg[5:])
            max = 100
            if value > max:
                value = max
            self.lego_sensors[port - 1] = value / float(max)
        elif len(msg) == 0:
            pass
        else:
            print('unknown msg: %s' % repr(msg))

if __name__ == '__main__':
    import time

    import connection
    bot = EV3Bot()
    bot.connect(connection.Socket('192.168.1.160'))
    #bot.connect(connection.Socket('10.162.177.187'))
    time.sleep(1)
    #bot.retina(True, bytes_in_timestamp=0)
    #bot.show_image()

    bot.activate_sensor([1, 2, 3, 4])


    import random
    while True:
        time.sleep(0.1)
        print(bot.lego_sensors)
        bot.motor(0, 0)
        bot.motor(1, 0)
        bot.motor(2, 0)
        #bot.retina(True)
        #bot.servo(0, random.uniform(-1, 1))
