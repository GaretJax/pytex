from collections import namedtuple

from base import Transformer

List = namedtuple("List", "depth type")


class RstProcessor(Transformer):
    list_stack = []
    inside_frame = False

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

    # End frame
    def end_frame(self):
        if self.inside_frame:
            self.print_line("\\end{frame}")
            self.inside_frame = False

    # Handle frames
    def handle_frames(self, line):
        stripped = line.rstrip()

        if stripped.startswith('.. frame:: '):
            self.end_frame()

            frame_name = stripped.replace('.. frame:: ', "")
            self.inside_frame = True

            return "\\begin{frame}[fragile]{" + frame_name + "}"
        elif stripped.startswith('.. sframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. sframe:: ', "")
            self.inside_frame = True

            self.print_line("\section{" + frame_name + "}")

            return "\\begin{frame}[fragile]{" + frame_name + "}"
        elif stripped.startswith('.. ssframe:: '):
            self.end_frame()

            frame_name = stripped.replace('.. ssframe:: ', "")
            self.inside_frame = True

            self.print_line("\subsection{" + frame_name + "}")

            return "\\begin{frame}[fragile]{" + frame_name + "}"
        elif stripped.startswith('.. toc::'):
            toc_name = stripped.replace('.. toc::', "")
            toc_name = toc_name.strip()

            # By default full TOC is shown
            if not toc_name:
                toc_name = "main"

            if toc_name == "main":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[hidesubsections]")
                self.print_line("\\end{frame}")
            elif toc_name == "current":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\tableofcontents[currentsection,hideothersubsections]")
                self.print_line("\\end{frame}")
            elif toc_name == "shallow":
                self.print_line("\\begin{frame}{Table of Contents}")
                self.print_line("\\begingroup");
                self.print_line("\\setcounter{tocdepth}{1}");
                self.print_line("\\tableofcontents[currentsection]");
                self.print_line("\\endgroup");
                self.print_line("\\end{frame}")

            return "";

        elif stripped.startswith('\end{document}'):
            self.end_frame()
        elif stripped.startswith('\section'):
            self.end_frame()
        elif stripped.startswith('\subsection'):
            self.end_frame()
        elif stripped.startswith('\subsubsection'):
            self.end_frame()

        return line

    # Handle some ReST style
    def handle_style(self, line, rst_begin, rst_end, latex):
        first_index = line.find(rst_begin)

        while first_index != -1:
            second_index = line.find(rst_end, first_index+len(rst_begin))

            if second_index == -1:
                break

            if second_index - first_index > len(rst_begin):
                line = line[:first_index] + \
                    "\\" + latex + "{" + \
                    line[first_index+len(rst_begin):second_index] + \
                    "}" + \
                    line[second_index+len(rst_end):]

            first_index = line.find(rst_begin, second_index+len(rst_end))

        return line

    # Handle inline code
    def handle_inline(self, line):
        return self.handle_style(line, ":code:`", "`", "cppi")

    # Handle bold
    def handle_bold(self, line):
        return self.handle_style(line, "**", "**", "textbf")

    # Handle emphasis
    def handle_emphasis(self, line):
        return self.handle_style(line, "*", "*", "textit")

    # Handle sections
    def handle_code(self, lines):
        inside_code = False

        for line in lines:
            stripped = line.rstrip()

            if stripped.startswith('.. code:: '):
                code = stripped.replace('.. code:: ', "")
                code = code.strip()

                if not code:
                    code = "cpp"

                inside_code = True

                self.print_line("%__rst_ignore__")
                self.print_line("\\begin{" + code + "code}")
            elif inside_code and not stripped.startswith('  '):
                inside_code = False
                self.print_line("\\end{" + code + "code}")
                self.print_line("%__rst_ignore__")
                self.print_line(line)
            else:
                self.print_line(line)

    # Handle sections
    def handle_sections(self, lines):
        levels = []

        ignored = False

        for i in range(len(lines) - 2):
            first_line = lines[i]
            second_line = lines[i+1]

            if "__rst_ignore__" in first_line:
                ignored = not ignored
                self.print_line(first_line)
                continue

            if ignored:
                self.print_line(first_line)
                continue

            if len(first_line) > 0 and len(second_line) > 0:
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
                        self.print_line("Section too deep:" + first_line)

                    lines[i+1] = ""
                else:
                    self.print_line(first_line)
            else:
                self.print_line(first_line)

        # Print the very last line
        self.print_line(lines[len(lines) - 1])

    # Process a single file
    def process_lines(self, lines, step):
        ignored = False

        # Handle code blocks
        if step is 0:
            self.handle_code(lines)

            return True

        # Handle sections
        if step is 1:
            self.handle_sections(lines)

            return True

        for line in lines:
            if "__rst_ignore__" in line:
                ignored = not ignored
                self.print_line(line)
                continue

            if ignored:
                self.print_line(line)
                continue

            # Handle frames
            if step is 2:
                self.print_line(self.handle_frames(line))

            # Handle lists
            if step is 3:
                self.print_line(self.handle_lists(line))

            # Handle styles
            if step is 4:
                # Handle inline code
                processed = self.handle_inline(line)

                # Handle bold
                processed = self.handle_bold(processed)

                # Handle emphasis
                processed = self.handle_emphasis(processed)

                self.print_line(processed)

        return step < 4
