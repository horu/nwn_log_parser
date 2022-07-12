import fcntl
import subprocess
import os
import typing

FILE_NAMES = [
    'nwclientLog1.txt',
    'nwclientLog2.txt',
    'nwclientLog3.txt',
    'nwclientLog4.txt',
]


class LogReader:
    def __init__(self, directory):
        self.processes = []
        for file_name in FILE_NAMES:
            # non block
            p = subprocess.Popen(['tail', '-f', directory + file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            fd = p.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
            self.processes.append(p)

    def read_lines(self):
        for p in self.processes:
            for line in p.stdout.readlines():
                decoded = line.decode()
                yield decoded
