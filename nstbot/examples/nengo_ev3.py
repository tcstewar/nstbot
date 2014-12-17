import nengo
import numpy as np

import nstbot

bot = nstbot.EV3Bot()
bot.connect(nstbot.connection.Socket('192.168.1.161'))

model = nengo.Network()
with model:
    stimulus = nengo.Node(np.sin)

    a = nengo.Ensemble(n_neurons=100, dimensions=1)
    nengo.Connection(stimulus, a)

    def servo(t, x):
        bot.servo(0, x[0], msg_period=0.1)
    nengo.Connection(a, nengo.Node(servo, size_in=1), synapse=0.01)

import nengo_gui.javaviz
jv = nengo_gui.javaviz.View(model)
sim = nengo.Simulator(model)
jv.update_model(sim)
jv.view()
while True:
    sim.run(1)
