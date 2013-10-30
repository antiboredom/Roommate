import pyaudio
# import wave
import signal
import struct
import sys
import time
from itertools import imap
from array import array

from urllib2 import urlopen
from urllib import urlencode


CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
BUFFER_SIZE = 128

OUTPUT_FILE = "data.csv"
THRESHOLD = 20000


# Add signal listener
def signal_handler(signal, frame):
        print ('Goodbye')
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


class Communicator:
    """Object for sending data to the sentient data"""
    def __init__(self, address):
        self.address = address

    def sendData(self, data):
        #debug
        message = urlencode(data)
        print(urlopen(self.address, message).read())


class ByteBuffer:
    """Buffer for sound objects"""
    def __init__(self, size, output_file):
        # FIXME: unpythonic type checking
        self.size = int(size)
        self.output_file = str(output_file)
        self.pointer = 0

        self.buffer_array = array('i', [0 for i in xrange(self.size)])

    def __enter__(self):
        return self

    def add(self, sample):
        self.buffer_array[self.pointer] = sample
        self.pointer += 1
        if self.pointer >= self.size:
            # debug
            c = Communicator("http://192.168.1.251:3000/Session/J-Room/Update/")
            data = {
                'updates': [{
                    'measureName': 'Sound',
                    'timeStamp': int(time.time()),
                    'value': int(self.buffer_array[0])}]}
            c.sendData(message=data)
        # /debug
            self.dump()
            self.pointer = 0

    def dump(self, size=None):
        size = size or self.size

        with open(self.output_file, "a+") as out_file:
            out_data = ','.join(imap(str, self.buffer_array))
            out_file.write(out_data)

    def __exit__(self):
        self.dump(size=self.pointer)


def get_amplitude(sample_block, absolute=True):
    format = "%dh" % (len(sample_block) / 2)
    shorts = struct.unpack(format, sample_block)
    if absolute:
        return [abs(x) for x in shorts]
    else:
        return shorts


def main():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK)

    with ByteBuffer(size=BUFFER_SIZE, output_file=OUTPUT_FILE) as buf:
        while True:
            data = get_amplitude(stream.read(CHUNK))
            buf.add(sum(imap(int, data))/len(data))  # integer division
            # print max(data)
            maxValue = max(data)
            if maxValue >= THRESHOLD:
                print ("Clip : %d" % maxValue)
            # print ("more")


if __name__ == '__main__':
    main()
