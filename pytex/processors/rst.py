from collections import namedtuple

from base import Transformer

List = namedtuple("List", "depth type")


class RstProcessor(Transformer):
    list_stack = []

    name = "RestructuredText processor"

    # Indicates if the processor wants to proces the given file or not
    def wants(self, source):
        return source.endswith('.tex.rst')

    # Get the target file name
    def target(self, source):
        return source.replace('.tex.rst', '.tex')

    # Checks that no list is still open
    def end(self):
        if self.list_stack:
            self.logger.error("Something went wrong in list handling")

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

    # Handle some ReST style
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

    # Handle sections
    def handle_sections(self, lines):
        levels = []

        for i in range(len(lines) - 2):
            first_line = lines[i]
            second_line = lines[i+1]

            if len(second_line) > 0:
                c = 0
                char = second_line[0]
                if char in ('#', '-', '_', '*', '+'):
                    while c < len(second_line) and second_line[c] is char:
                        c = c + 1

                if c >= 3 and c <= len(first_line):
                    if char not in levels:
                        levels.append(char)

                    index = levels.index(char)

                    if index is 0:
                        self.print_line("\section{" + first_line + "}")
                    elif index is 1:
                        self.print_line("\subsection{" + first_line + "}")
                    elif index is 2:
                        self.print_line("\subsubsection{" + first_line + "}")
                    else:
                        self.print_line("Section too dep:" + first_line)

                    lines[i+1] = ""
                else:
                    self.print_line(first_line)
            else:
                self.print_line(first_line)

        # Print the very last line
        self.print_line(lines[len(lines) - 1])

    # Process a single line
    def process_lines(self, lines, step):
        # Handle sections
        if step is 0:
            self.handle_sections(lines)

            return True

        # Handle lists
        if step is 1:
            for line in lines:
                self.print_line(self.handle_lists(line))

            return True

        # Handle styles
        if step is 2:
            for line in lines:
                # Handle bold
                processed = self.handle_bold(line)

                # Handle emphasis
                processed = self.handle_emphasis(processed)

                self.print_line(processed)

            return False
