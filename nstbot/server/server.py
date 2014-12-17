import socket
import re

class Command(object):
    def __init__(self, regex, function):
        self.matcher = re.compile(regex)
        self.function = function

class NSTServer(object):
    def __init__(self, port=56000, buffer_size=1024):
        self.port = port
        self.buffer_size = buffer_size
        self.commands = []

        self.commands.append(Command('[?][?]', self.help))

    def send(self, msg):
        self.conn.sendall(msg + '\r\n')

    def run(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', self.port))  # allow connections from anywhere
        self.socket.listen(1)              # only allow one connection

        while True:
            try:
                self.conn, self.addr = self.socket.accept()
                self.send(self.welcome_message())
                msg = ''
                while True:
                    msg = msg + self.conn.recv(self.buffer_size)
                    if len(msg) == 0:
                        # client has disconnected
                        break
                    print 'msg:', `msg`
                    index = msg.find('\n')
                    while index > -1:
                        cmd = msg[:index]
                        msg = msg[index + 1:]
                        self.process_command(cmd.strip())
                        index = msg.find('\n')
            finally:
                self.conn.close()

    def welcome_message(self):
        return '''NST robot interface.  Type '??' and hit <enter> for help.'''

    def process_command(self, cmd):
        print 'processing command:', `cmd`
        for command in self.commands:
            m = command.matcher.match(cmd)
            if m is not None:
                command.function()

    def help(self):
        self.send("here is some help")



if __name__ == '__main__':
    NSTServer().run()



