import nstbot
import numpy as np
import thread

class RetinaBot(nstbot.NSTBot):
    def initialize(self):
        super(RetinaBot, self).initialize()
        self.retina(False)
        self.retina_packet_size = None
        self.image = None
        self.count_spike_regions = None
        self.track_periods = None

    def connect(self, connection):
        super(RetinaBot, self).connect(connection)
        thread.start_new_thread(self.sensor_loop, ())

    def disconnect(self):
        self.retina(False)
        super(RetinaBot, self).disconnect()

    def retina(self, active, bytes_in_timestamp=4):
        if active:
            cmd = '!E%d\nE+\n' % bytes_in_timestamp
            self.retina_packet_size = 2 + bytes_in_timestamp
        else:
            cmd = 'E-\n'
            self.retina_packet_size = None
        self.connection.send(cmd)

    def show_image(self, decay=0.5, display_mode='quick'):
        if self.image is None:
            self.image = np.zeros((128, 128), dtype=float)
            thread.start_new_thread(self.image_loop, (decay, display_mode))

    def image_loop(self, decay, display_mode):
        import pylab
        fig = pylab.figure()
        pylab.ion()
        img = pylab.imshow(self.image, vmax=1, vmin=-1,
                                       interpolation='none', cmap='binary')
        pylab.xlim(0, 127)
        pylab.ylim(127, 0)

        regions = {}
        if self.count_spike_regions is not None:
            for k, v in self.count_spike_regions.items():
                minx, miny, maxx, maxy = v
                rect = pylab.Rectangle((minx - 0.5, miny - 0.5),
                                       maxx - minx,
                                       maxy - miny,
                                       facecolor='yellow', alpha=0.2)
                pylab.gca().add_patch(rect)
                regions[k] = rect

        if self.track_periods is not None:
            colors = ([(0,0,1), (0,1,0), (1,0,0), (1,1,0), (1,0,1)] * 10)[:len(self.p_y)]
            scatter = pylab.scatter(self.p_x, self.p_y, s=50, c=colors)
        else:
            scatter = None

        while True:
            img.set_data(self.image)

            for k, rect in regions.items():
                alpha = self.get_spike_rate(k) * 0.5
                alpha = min(alpha, 0.5)
                rect.set_alpha(0.05 + alpha)
            if scatter is not None:
                scatter.set_offsets(np.array([self.p_x, self.p_y]).T)
                c = [(r,g,b,min(self.track_certainty[i],1)) for i,(r,g,b) in enumerate(colors)]
                scatter.set_color(c)

            if display_mode == 'quick':
                # this is much faster, but doesn't work on all systems
                fig.canvas.draw()
                fig.canvas.flush_events()
            else:
                # this works on all systems, but is kinda slow
                pylab.pause(0.001)

            self.image *= decay


    def sensor_loop(self):
        """Handle all data coming from the robot."""
        old_data = None
        buffered_ascii = ''
        while True:
            packet_size = self.retina_packet_size
            # grab the new data
            data = self.connection.receive()

            # combine it with any leftover data from last time through the loop
            if old_data is not None:
                data = old_data + data
                old_data = None

            if packet_size is None:
                # no retina events, so everything should be ascii
                buffered_ascii += data
            else:
                # find the ascii events
                data_all = np.fromstring(data, np.uint8)
                ascii_index = np.where(data_all[::packet_size] < 0x80)[0]

                offset = 0
                while len(ascii_index) > 0:
                    # if there's an ascii event, remove it from the data
                    index = ascii_index[0]*packet_size
                    stop_index = np.where(data_all[index:] >=0x80)[0]
                    if len(stop_index) > 0:
                        stop_index = index + stop_index[0]
                    else:
                        stop_index = len(data)

                    # and add it to the buffered_ascii list
                    buffered_ascii += data[offset+index:offset+stop_index]
                    data_all = np.hstack((data_all[:index],
                                          data_all[stop_index:]))
                    offset += stop_index - index
                    ascii_index = np.where(data_all[::packet_size] < 0x80)[0]

                # handle any partial retina packets
                extra = len(data_all) % packet_size
                if extra != 0:
                    old_data = data[-extra:]
                    data_all = data_all[:-extra]
                if len(data_all) > 0:
                    # now process those retina events
                    self.process_retina(data_all)

            # and process the ascii events too
            while '\n' in buffered_ascii:
                cmd, buffered_ascii = buffered_ascii.split('\n', 1)
                self.process_ascii(cmd)

    def process_ascii(self, message):
        print 'ascii', `message`

    last_timestamp = None
    def process_retina(self, data):
        packet_size = self.retina_packet_size
        y = data[::packet_size] & 0x7f
        x = data[1::packet_size] & 0x7f
        if self.image is not None:
            value = np.where(data[1::packet_size]>=0x80, 1, -1)
            self.image[y, x] += value

        if self.count_spike_regions is not None:
            tau = 0.05 * 1000000
            for k, region in self.count_spike_regions.items():
                minx, miny, maxx, maxy = region
                index = (minx <= x) & (x<maxx) & (miny <= y) & (y<maxy)
                count = np.sum(index)
                t = (int(data[-2]) << 8) + data[-1]
                if packet_size >= 5:
                    t += int(data[-3]) << 16
                if packet_size >= 6:
                    t += int(data[-4]) << 24

                old_count, old_time = self.count_regions[k]

                dt = float(t - old_time)
                if dt < 0:
                    dt += 1 << ((packet_size - 2) * 8)
                count *= self.count_regions_scale[k]
                count /= dt / 1000.0

                decay = np.exp(-dt/tau)
                new_count = old_count * (decay) + count * (1-decay)

                self.count_regions[k] = new_count, t

        if self.track_periods is not None:
            t = data[2::packet_size].astype(np.uint32)
            t = (t << 8) + data[3::packet_size]
            if packet_size >= 5:
                t = (t << 8) + data[4::packet_size]
            if packet_size >=6:
                t = (t << 8) + data[5::packet_size]

            if self.last_timestamp is not None:
                dt = float(t[-1]) - self.last_timestamp
                if dt < 0:
                    dt += 1 << (8 * (packet_size-2))
            else:
                dt = 1
            self.last_timestamp = t[-1]

            index_on = (data[1::packet_size] & 0x80) > 0
            #index_off = (data[1::packet_size] & 0x80) == 0

            delta = np.where(index_on, t - self.last_on[x, y], 0)

            self.last_on[x[index_on],
                         y[index_on]] = t[index_on]
            #self.last_off[x[index_off],
            #              y[index_off]] = t[index_off]

            tau = 0.05 * 1000000
            decay = np.exp(-dt/tau)
            self.track_certainty *= decay

            for i, period in enumerate(self.track_periods):
                eta = self.track_eta
                t_exp = period * 2
                sigma_t = self.track_sigma_t    # in microseconds
                sigma_p = self.track_sigma_p    # in pixels
                t_diff = delta.astype(np.float) - t_exp

                w_t = np.exp(-(t_diff**2)/(2*sigma_t**2))
                px = self.p_x[i]
                py = self.p_y[i]

                dist2 = (x - px)**2 + (y - py)**2
                w_p = np.exp(-dist2/(2*sigma_p**2))

                ww = w_t * w_p
                c = sum(ww) * self.track_certainty_scale / dt

                self.track_certainty[i] += (1-decay) * c

                w = eta * ww
                for j in np.where(w > 0.02)[0]:
                        px += w[j] * (x[j] - px)
                        py += w[j] * (y[j] - py)
                self.p_x[i] = px
                self.p_y[i] = py

                '''
                # faster, but less accurate method:
                # update position estimate
                try:
                    r_x = np.average(x, weights=w_t*w_p)
                    r_y = np.average(y, weights=w_t*w_p)
                    self.p_x[i] = (1-eta)*self.p_x[i] + (eta)*r_x
                    self.p_y[i] = (1-eta)*self.p_y[i] + (eta)*r_y
                except ZeroDivisionError:
                    # occurs in np.average if weights sum to zero
                    pass
                '''

            #print self.p_x, self.p_y, self.track_certainty


    def track_spike_rate(self, **regions):
        self.count_spike_regions = regions
        self.count_regions = {}
        self.count_regions_scale = {}
        for k,v in regions.items():
            self.count_regions[k] = [0, 0]
            area = (v[2] - v[0]) * (v[3] - v[1])
            self.count_regions_scale[k] = 200.0 / area

    def get_spike_rate(self, region):
        return self.count_regions[region][0]

    def track_frequencies(self, freqs, sigma_t=100, sigma_p=30, eta=0.3,
                                 certainty_scale=10000):
        freqs = np.array(freqs, dtype=float)
        track_periods = 500000/freqs
        self.track_certainty_scale = certainty_scale

        self.track_sigma_t = sigma_t
        self.track_sigma_p = sigma_p
        self.track_eta = eta

        self.last_on = np.zeros((128, 128), dtype=np.uint32)
        self.last_off = np.zeros((128, 128), dtype=np.uint32)
        self.p_x = np.zeros_like(track_periods) + 64.0
        self.p_y = np.zeros_like(track_periods) + 64.0
        self.track_certainty = np.zeros_like(track_periods)
        self.good_events = np.zeros_like(track_periods, dtype=int)
        self.track_periods = track_periods

    def get_frequency_info(self, index):
        x = self.p_x[index] / 64.0 - 1
        y = - self.p_y[index] / 64.0 + 1
        return x, y, self.track_certainty[index]




if __name__ == '__main__':
    import connection
    bot = RetinaBot()
    bot.connect(connection.Serial('/dev/ttyUSB0', baud=4000000))
    bot.retina(True)
    bot.show_image()
    bot.track_spike_rate(
                         #all=(0,0,128,128),
                         left=(0,0,64,128),
                         right=(64,0,128,128))
    bot.track_frequencies(freqs=[200, 300, 400])
    import time
    while True:
        time.sleep(1)

