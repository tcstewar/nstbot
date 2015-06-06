from nstbot.nengo.pushbot_network import PushBotNetwork
import nstbot
import numpy as np
import nengo

model = nengo.Network()
with model:
    stim = nengo.Node(np.sin)
    bot = PushBotNetwork(
            #nstbot.Socket('10.162.177.135'),
            nstbot.Serial('/dev/ttyUSB0', baud=4000000),
            motor=True, laser=True, retina=True, freqs=[100, 200, 300])

    #nengo.Connection(stim, bot.motor[0])
    nengo.Connection(stim, bot.laser)

sim = nengo.Simulator(model)
sim.run(10)



