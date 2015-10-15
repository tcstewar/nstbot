import numpy as np

# Nengo imports
from nengo.params import Parameter

# Rig imports
from rig.bitfield import (
    BitField, UnavailableFieldError
)

from rig.machine import Links

from rig.place_and_route.constraints import (
    LocationConstraint, RouteEndpointConstraint
)

# Nengo SpiNNaker imports
from nengo_spinnaker.netlist import (
    Net, Vertex
)

from nengo_spinnaker.builder.builder import (
    Model, ObjectPort, spec
)

from nengo_spinnaker.builder.model import (
    InputPort, OutputPort, SignalParameters
)

from nengo_spinnaker.builder.node import PassthroughNodeTransmissionParameters

from nengo_spinnaker.operators.filter import (
    Filter
)

from nengo_spinnaker.operators.mc_player import (
    MulticastPacketSender, Packet
)

from nengo_spinnaker.utils.config import getconfig

from . import pushbot_network

@Model.builders.register(pushbot_network.MotorNode)
def build_motor(model, motor):
    print("Building motor node")

    # Get or create parent NST bot keyspace
    keyspace = get_create_nstbot_keyspace(model)

    # Get or create MC player and offchip vertex associated with bot
    mc_player, offchip_vertex = get_create_mc_player_offchip_vertex(model, motor)

    # Create child keyspace with motor-specific fields
    motor_keyspace = keyspace(payload_format=0, command_id=32)

    # Create a 2D filter to drive the motor
    # (push-bot only accepts source of input per timestep)
    motor_filter = Filter(2)
    model.object_operators[motor] = motor_filter

    # Add connection to model
    model.connection_map.add_connection(motor_filter, OutputPort.standard,
                                        SignalParameters(latching=True, keyspace=motor_keyspace),
                                        PassthroughNodeTransmissionParameters(np.eye(2) * 100.0),
                                        offchip_vertex, None, None)

    # Create key for command to turn on and off motors and
    enable_disable_motor_key = keyspace(payload_format=0, command_id=2, index=0, cluster=0)
    mc_player.start_packets.append(Packet(enable_disable_motor_key, 1))
    mc_player.end_packets.append(Packet(enable_disable_motor_key, 0))


@Model.sink_getters.register(pushbot_network.MotorNode)
def get_motor_sink(model, conn):
    print("Sinking connection into motor")
    # Motor will be replaced with a filter to combine the output of
    # multiple inputs during build_motor so simply connect input
    # to filter's standard input port
    motor = model.object_operators[conn.post_obj]
    return spec(ObjectPort(motor, InputPort.standard))


#@Model.sink_getters.register(pushbot_network.LaserNode)
#def get_laser_sink(model, conn):
#    pass

@Model.sink_getters.register(pushbot_network.BeepNode)
def get_beep_sink(model, conn):
    '''
    Builder.register_connectivity_transform(robot.ActuatorTransform(
        beep.Beep,
        robot.pwm_keyspace(i=36, p=0),  # Keyspace on filter->pushbot
        1000.0 / 2.0**15,  # Convert to mHz
        mc_to_pushbot_stop_keyspaces_payloads=[
            (robot.motor_keyspace(i=2, p=0, q=0, d=0), 0)  # Beeper off
        ],
        filter_args={'size_in': 2, 'transmission_period': 100}
    ))
    '''
    pass


def get_create_mc_player_offchip_vertex(model, pushbot_node):
    bot = pushbot_node.bot
    print("Bot:", bot)
    # If MC player hasn't already been instantiated
    # **TODO** checks for mc_player
    if bot not in model.object_operators:
        print("Bot not present")
        mc_player = MulticastPacketSender()
        model.object_operators[bot] = mc_player

        # Get or create parent NST bot keyspace
        keyspace = get_create_nstbot_keyspace(model)

        # Get route and location from config associated
        # with the bot that owns the actuator
        # **TODO** defaults/safety/errors
        route_to_bot = getconfig(model.config, bot, "route_to_bot", None)
        bot_location = getconfig(model.config, bot, "bot_location", None)

        # Build vertex constrained to bot location and route
        bot.offchip_vertex = Vertex()
        bot.offchip_vertex.contraints = [
            LocationConstraint(bot.offchip_vertex, bot_location),
            RouteEndpointConstraint(bot.offchip_vertex, route_to_bot),
        ]

        model.extra_vertices.append(bot.offchip_vertex)

        # Connect MC player to offchip vertex
        model.extra_nets.append(
            Net(mc_player, bot.offchip_vertex, 0, keyspace)
        )

    # Return MC player
    return model.object_operators[bot], bot.offchip_vertex

def get_create_nstbot_keyspace(model):
    # Get NST bot keyspace
    # **NOTE** keyspaces is defaultdict-derived so this will
    # be empty the first time this function is called
    # **TODO** munge in location and route
    keyspace = model.keyspaces["nstbot"]

    # **YUCK** determine if keyspace has been initialise
    # by querying command_id field (arbitrarily)
    try:
        command_id = keyspace.command_id
    except UnavailableFieldError:
        print "Building robot keyspace"
        # If it fails add keyspace fields
        keyspace.add_field("index", length=3, start_at=0)
        keyspace.add_field("payload_format", length=1, start_at=3)
        keyspace.add_field("command_id", length=7, start_at=4)

        # **YUCK** cluster field is required by keyspace region writing
        keyspace.add_field("cluster", length=1)

    return keyspace

def add_spinnaker_params(config):
    """Add SpiNNaker specific parameters to a configuration object."""
    # Add simulator parameters
    config.configures(pushbot_network.PushBotNetwork)

    config[pushbot_network.PushBotNetwork].set_param("bot_location", Parameter(default=(1, 0)))
    config[pushbot_network.PushBotNetwork].set_param("route_to_bot", Parameter(default=Links.east))