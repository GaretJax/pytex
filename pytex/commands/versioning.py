import os
import shlex
import subprocess
import tempfile

from pytex.subcommands import Command


class Versions(Command):
    name = "versions"
    help = "Show all the tags present in the current document."

    def parser(self):
        parser = self.parser_class()
        parser.add_argument("-c", "--current")
        parser.add_argument(
            "-l", "--latex", action="store_const", const=True, default=False
        )
        parser.add_argument(
            "-f",
            "--format",
            default='{0.name} - {0.tagger[0]} | "{0.message}"',
        )
        return parser

    def execute(self, args):
        tags = reversed(self.versions().get_tags())

        if args.latex:
            self._latex(args, tags)
        else:
            self._console(args, tags)

    def _latex(self, args, tags):
        for t in tags:
            date = t.date.strftime("%B %d, %Y")
            # TODO: That's dangerous...
            message = t.message.replace("&", r"\&")
            author = t.tagger[0].replace("&", r"\&")
            print(
                r"{} & {} & {} \tabularnewline".format(date, author, message)
            )

    def _console(self, args, tags):
        for t in tags:
            print(args.format.format(t))


versions_command = Versions()


class Save(Command):

    name = "save"
    help = "Saves the current version of the document in a single commit."

    def parser(self):
        parser = self.parser_class()
        parser.add_argument("-m", "--message")
        return parser

    def execute(self, args):
        message = args.message

        if not message:
            message = self.config.get("versioning", "commitmessage")

        self.versions().addall().commit(message)


saving_command = Save()


class Pull(Command):

    name = "pull"
    help = "Pull changes from remote repository"

    def parser(self):
        parser = self.parser_class()
        return parser

    def execute(self, args):
        self.versions().pull()


pull_command = Pull()


class Push(Command):

    name = "push"
    help = "Push changes to remote repository"

    def parser(self):
        parser = self.parser_class()
        return parser

    def execute(self, args):
        self.versions().push()


push_command = Push()


class Sync(Command):

    name = "sync"
    help = "Synchronize with the remote directory (commit -> pull -> push)"

    def parser(self):
        parser = self.parser_class()
        parser.add_argument("-m", "--message")
        return parser

    def execute(self, args):
        message = args.message

        if not message:
            message = self.config.get("versioning", "commitmessage")

        self.versions().addall().commit(message)

        self.versions().pull()
        self.versions().push()


sync_command = Sync()


class Tag(Command):

    name = "tag"
    help = (
        "Creates a tagged version of the document"
        "out of the currently active commit."
    )

    def parser(self):
        parser = self.parser_class()
        parser.add_argument("name")
        parser.add_argument("-m", "--message")
        return parser

    def get_message(self):
        fd, path = tempfile.mkstemp()

        try:
            os.close(fd)
            cmd = shlex.split(self.config.get("general", "editor")) + [path]
            subprocess.check_call(cmd)
            with open(path) as fh:
                message = fh.read().strip()
        finally:
            os.remove(path)

        return message

    def execute(self, args):
        message = args.message
        if not message:
            message = self.get_message()

        self.versions().tag(args.name, message)


tagging_command = Tag()
