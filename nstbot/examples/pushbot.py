import nstbot


bot = nstbot.PushBot()
#bot.connect(connection.Serial('/dev/ttyUSB0', baud=4000000))
bot.connect(nstbot.Socket('10.162.177.135'))
bot.laser(150)
bot.track_frequencies(freqs=[50, 100, 150])
bot.retina(True)
bot.show_image()
#bot.track_spike_rate(all=(0,0,128,128))
import time
while True:
    time.sleep(1)
    bot.motor(-0.05, 0.05)
