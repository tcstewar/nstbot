import nstbot

import time
bot = nstbot.RetinaBot()
bot.connect(nstbot.Serial('/dev/ttyUSB0', baud=4000000))
#bot.connect(connection.Socket('10.162.177.187'))
#bot.connect(nstbot.Socket('192.168.1.161'))
time.sleep(1)
bot.retina(True)
bot.show_image()
#bot.track_spike_rate(
#                     #all=(0,0,128,128),
#                     left=(0,0,64,128),
#                     right=(64,0,128,128))
#bot.track_frequencies(freqs=[200, 300, 400])
while True:
    time.sleep(1)

