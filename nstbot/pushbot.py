import retinabot

class PushBot(retinabot.RetinaBot):
    def initialize(self):
        super(PushBot, self).initialize()
        self.laser(0)
        self.beep(0)
        self.motor(0, 0)
        #self.led(0)
        self.connection.send('!M+\n')
    def disconnect(self):
        self.laser(0)
        self.beep(0)
        self.motor(0, 0)
        self.led(0)
        super(PushBot, self).disconnect()

    def laser(self, freq, msg_period=None):
        if freq <= 0:
            cmd = '!PA=0\n!PA0=0\n'
        else:
            cmd = '!PA=%d\n!PA0=%d\n' % (int(1000000/freq),
                                         int(500000/freq))
        self.send('laser', cmd, msg_period=msg_period)

    def motor(self, left, right, msg_period=None):
        left = int(left*100)
        right = int(right*100)
        if left > 100: left=100
        if left < -100: left=-100
        if right > 100: right=100
        if right < -100: right=-100
        cmd = '!MVD0=%d\n!MVD1=%d\n' % (left, right)
        self.send('motor', cmd, msg_period=msg_period)

    def beep(self, freq, msg_period=None):
        if freq <= 0:
            cmd = '!PB=0\n!PB0=0\n'
        else:
            cmd = '!PB=%d\n!PB0=%%50\n' % int(1000000/freq)
        self.send('beep', cmd, msg_period)

    def led(self, freq, msg_period=False):
        if freq <= 0:
            cmd = '!PC=0\n!PC0=0\n!PC1=0\n'
        else:
            cmd = '!PC=%d\n!PC0=%d\n!PC1=%d\n' % (int(1000000/freq),
                    int(500000/freq), int(500000/freq))
        print 'led', cmd

        self.send('led', cmd, msg_period)



if __name__ == '__main__':
    import connection
    bot = PushBot()
    #bot.connect(connection.Serial('/dev/ttyUSB0', baud=4000000))
    bot.connect(connection.Socket('10.162.177.135'))
    bot.laser(150)
    bot.track_frequencies(freqs=[50, 100, 150])
    bot.retina(True)
    bot.show_image()
    #bot.track_spike_rate(all=(0,0,128,128))
    import time
    while True:
        time.sleep(1)
        bot.motor(-0.05, 0.05)
