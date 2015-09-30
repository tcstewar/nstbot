from .retinabot import RetinaBot
from .pushbot import PushBot
from .ev3bot import EV3Bot
from . import connection
from .connection import Socket, Serial
import nengo
from nengo.pushbot_network import PushBotNetwork

# Attempt to inport SpiNNaker builder code
#try:
from nengo import spinnaker

from nengo.spinnaker import add_spinnaker_params
#except ImportError:
#    print "MERDE"
#    #pass