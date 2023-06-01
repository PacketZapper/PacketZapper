#!/usr/bin/env python
import errno
import os
import time
CMD = "whsniff -c 25 | tshark -l -T ek -i - | cat > /tmp/fifo1"
FIFO = '/tmp/fifo1'
es_list = []

try:
    os.mkfifo(FIFO)
except OSError as e:
    if e.errno != errno.EEXIST:
        raise e

print("Opening FIFO...")
with open(FIFO, 'r') as fifo:
    print("FIFO opened")
    while True:
        for line in fifo.readlines(2):
            print(line)

print("end of read program")