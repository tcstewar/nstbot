import nengo
import nstbot

bot = nstbot.PushBot()
bot.connect(nstbot.Socket('10.162.177.135'))

model = nengo.Network()
with model:
    motors = nengo.Node([0]*2)

    def bot_control(t, x):
        bot.motor(x[0], x[1])
    bot_c = nengo.Node(bot_control, size_in=2)

    nengo.Connection(motors, bot_c)

