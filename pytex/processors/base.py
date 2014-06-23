import sys


class Processor(object):

    def process_file(self, source, target):
        with open(target, 'w') as self.f:
            with open(source, 'r') as sourcefile:
                for line in sourcefile.read().splitlines():
                    self.process_line(line)

    def process_file_out(self, source):
        self.f = sys.stdout

        with open(source, 'r') as sourcefile:
            for line in sourcefile.read().splitlines():
                self.process_line(line)
