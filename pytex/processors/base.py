import sys


class Transformer(object):

    def run(self, source):
        with open(source, 'r') as sourcefile:
            for line in sourcefile.read().splitlines():
                self.process_line(line)

        try:
            self.end()
        except AttributeError:
            # This method is optional in subclass
            pass

    def process_file(self, source):
        target = self.target(source)

        self.logger.info("Process {} with {}".format(source, self.name))

        with open(target, 'w') as self.f:
            self.run(source)

    def process_file_out(self, source):
        self.f = sys.stdout

        self.run(source)
