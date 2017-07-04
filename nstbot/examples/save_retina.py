import nstbot

import time
bot = nstbot.RetinaBot()
#bot.connect(nstbot.Serial('/dev/ttyUSB0', baud=4000000))
bot.connect(nstbot.Serial('COM6', baud=4000000))
#bot.connect(connection.Socket('10.162.177.187'))
#bot.connect(nstbot.Socket('192.168.1.161'))
time.sleep(1)
bot.retina(True)

filename = time.strftime('retina-%Y%m%d-%H%M%S.dat')

bot.record_retina_data(filename)
print('Recording to %s' % filename)


while True:
    time.sleep(1)

