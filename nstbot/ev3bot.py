import nstbot

class EV3Bot(nstbot.NSTBot):
    def initialize(self):
        super(EV3Bot, self).initialize()
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


if __name__ == '__main__':
    import connection
    bot = EV3Bot()
    bot.connect(connection.Socket('192.168.1.161'))

    import time
    import random
    while True:
        time.sleep(1)
        bot.servo(0, random.uniform(-1, 1))
