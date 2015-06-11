import nstbot
import numpy as np
import nengo


model = nengo.Network()
with model:
    bot = nstbot.PushBotNetwork(
            nstbot.Socket('10.162.177.135'),
            motor=True, laser=True, retina=False, freqs=[100, 200, 300],
            beep=True)

    #nengo.Connection(stim, bot.motor[0])
    motor = nengo.Node([0,0])
    nengo.Connection(motor, bot.motor)

    beep = nengo.Node([0])
    nengo.Connection(beep, bot.beep)

