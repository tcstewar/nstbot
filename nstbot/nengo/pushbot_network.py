import nengo
import numpy as np

import nstbot

class MotorNode(nengo.Node):
    def __init__(self, bot):
        super(MotorNode, self).__init__(self.motor, size_in=2, size_out=0)
        self.bot = bot

    def motor(self, t, x):
        self.bot.motor(x[0], x[1])

class PushBotNetwork(nengo.Network):
    def __init__(self, connection, motor=False):
        self.bot = nstbot.PushBot()
        self.bot.connect(connection)

        if motor:
            self.motor = MotorNode(self.bot)

if __name__ == '__main__':
    import nengo

    model = nengo.Network()
    with model:
        stim = nengo.Node(np.sin)
        bot = PushBotNetwork(nstbot.Socket('10.162.177.135'), motor=True)

        nengo.Connection(stim, bot.motor[0])

    sim = nengo.Simulator(model)
    sim.run(10)


