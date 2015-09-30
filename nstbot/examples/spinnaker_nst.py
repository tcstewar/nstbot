import nengo
import nengo_spinnaker
import numpy as np

import nstbot

from rig.machine import Links

network = nengo.Network()
with network:
    motor_input = nengo.Node([1.0, 1.0])
    bot_network = nstbot.PushBotNetwork(motor=True)

    nengo.Connection(motor_input, bot_network.motor)

nstbot.add_spinnaker_params(network.config)
nengo_spinnaker.add_spinnaker_params(network.config)
network.config[bot_network].route_to_bot = Links.east
network.config[bot_network].bot_location = (1, 0)

sim = nengo_spinnaker.Simulator(network)
with sim:
    sim.run(10.0)
