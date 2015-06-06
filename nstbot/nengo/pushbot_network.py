import nengo
import numpy as np

import nstbot

class MotorNode(nengo.Node):
    def __init__(self, bot, msg_period):
        super(MotorNode, self).__init__(self.motor, size_in=2, size_out=0)
        self.bot = bot
        self.msg_period = msg_period

    def motor(self, t, x):
        self.bot.motor(x[0], x[1], msg_period=self.msg_period)

class LaserNode(nengo.Node):
    def __init__(self, bot, msg_period):
        super(LaserNode, self).__init__(self.laser, size_in=1, size_out=0)
        self.bot = bot
        self.msg_period = msg_period

    def laser(self, t, x):
        self.bot.laser(x[0] * 1000, msg_period=self.msg_period)


class PushBotNetwork(nengo.Network):
    def __init__(self, connection, msg_period=0.01,
                 motor=False, laser=False):
        self.bot = nstbot.PushBot()
        self.bot.connect(connection)

        if motor:
            self.motor = MotorNode(self.bot, msg_period=msg_period)
        if laser:
            self.laser = LaserNode(self.bot, msg_period=msg_period)

if __name__ == '__main__':
    import nengo

    model = nengo.Network()
    with model:
        stim = nengo.Node(np.sin)
        bot = PushBotNetwork(nstbot.Socket('10.162.177.135'),
                             motor=True, laser=True)

        #nengo.Connection(stim, bot.motor[0])
        nengo.Connection(stim, bot.laser)

    sim = nengo.Simulator(model)
    sim.run(10)


