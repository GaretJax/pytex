import sys
import os


class Transformer(object):
    processed_lines = []

    # Process the file and outputs the result to self.
    def run(self, source):
        with open(source, 'r') as sourcefile:
            source_lines = sourcefile.read().splitlines()

        step = 0
        while self.process_lines(source_lines, step):
            source_lines = self.processed_lines
            self.processed_lines = []
            step = step + 1

        for line in self.processed_lines:
            self.f.write(line)
            self.f.write(os.linesep)

        try:
            self.end()
        except AttributeError:
            # This method is optional in subclass
            pass

        self.processed_lines = []

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

    # print a line (save it for later)
    def print_line(self, line):
        self.processed_lines.append(line)
