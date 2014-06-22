class Processor(object):

    def process_file(self, source, target):
        self.f = open(target, 'w')

        for line in open(source, 'r').read().splitlines():
            self.process_line(line)

        self.f.close()
