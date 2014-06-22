import os

from collections import namedtuple

from base import Processor

List = namedtuple("List", "depth type")

test = Processor()

class RstProcessor(Processor):
    list_stack = []

    def print_line(self, line):
        self.f.write(line)
        self.f.write(os.linesep)

    # start a list
    def start_list(self, depth, type):
        self.list_stack.append(List(depth, type))

        if type == 1:
            self.print_line("\\begin{itemize}")
        elif type == 2:
            self.print_line("\\begin{enumerate}")


    # end the previous list
    def end_list(self):
        prev = self.list_stack[-1]

        if prev.type == 1:
            self.print_line("\\end{itemize}")
        elif prev.type == 2:
            self.print_line("\\end{enumerate}")

        self.list_stack.pop()


    # Handle a list item
    def handle_item(self, depth, type):
        if self.list_stack:
            prev = self.list_stack[-1]

            if prev.type == type:
                if prev.depth < depth:
                    self.start_list(depth, type)
                else:
                    while prev.depth > depth:
                        self.end_list()

                        if not self.list_stack:
                            break

                        prev = self.list_stack[-1]

                    if not self.list_stack:
                        self.start_list(depth, type)

            else:
                if prev.depth == depth:
                    self.end_list()
                    self.start_list(depth, type)
                elif prev.depth < depth:
                    self.start_list(depth, type)
                else:
                    while prev.depth > depth:
                        self.end_list()

                        if not self.list_stack:
                            break

                        prev = self.list_stack[-1]

                    if not self.list_stack:
                        self.start_list(depth, type)

        else:
            self.start_list(depth, type)


    # Handle lists
    def handle_lists(self, line):
        stripped = line.lstrip()

        # Compute the depth of the list based on the number of spaces
        # before the * char
        depth = len(line) - len(stripped)

        if stripped.startswith('1.'):
            self.handle_item(depth, 2)

            return "\item " + stripped.replace("1.", "", 1)

        elif stripped.startswith('*'):
            self.handle_item(depth, 1)

            return "\item " + stripped.replace("*", "", 1)

        else:
            while self.list_stack:
                self.end_list()

            return line


    def handle_style(self, line, rst, latex):
        first_index = line.find(rst)

        while first_index != -1:
            second_index = line.find(rst, first_index+len(rst))

            if second_index == -1:
                break

            if second_index - first_index > len(rst):
                line = line[:first_index] + \
                    "\\" + latex + "{" + \
                    line[first_index+len(rst):second_index] + \
                    "}" + \
                    line[second_index+len(rst):]

            first_index = line.find(rst, second_index+len(rst))

        return line


    # Handle bold
    def handle_bold(self, line):
        return self.handle_style(line, "**", "textbf")


    # Handle emphasis
    def handle_emphasis(self, line):
        return self.handle_style(line, "*", "textit")


    # Process a single line 
    def process_line(self, line):
        # Handle lists
        processed = self.handle_lists(line)

        # Handle bold
        processed = self.handle_bold(processed)

        # Handle emphasis
        processed = self.handle_emphasis(processed)

        self.print_line(processed)
