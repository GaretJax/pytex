import sys


class Transformer(object):

    # Process the file and outputs the result to self.
    def run(self, source):
        with open(source, 'r') as sourcefile:
            for line in sourcefile.read().splitlines():
                self.process_line(line)

        try:
            self.end()
        except AttributeError:
            # This method is optional in subclass
            pass

    # Process file and write the result to the transformed file
    def process_file(self, source):
        target = self.target(source)

        self.logger.info("Process {} with {}".format(source, self.name))

        with open(target, 'w') as self.f:
            self.run(source)

    # Process file and outputs the results on the command line
    def process_file_out(self, source):
        self.f = sys.stdout

        self.run(source)
