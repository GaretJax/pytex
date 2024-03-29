import os
import sys

from pytex.subcommands import Command


class List(Command):

    name = "list-templates"
    help = "List the currently available templates."

    def execute(self, args):
        path = self.config.get("templates", "directory")
        path = os.path.expanduser(path)

        for name in os.listdir(path):
            # Ignore hidden files
            if name.startswith("."):
                continue
            if name == "README":
                continue
            print(name, file=sys.__stdout__)


list_command = List()


class Update(Command):

    name = "update-templates"
    help = (
        "Updates the current templates set by pulling "
        "the latest changes from the remote git repository."
    )

    def execute(self, args):
        raise NotImplementedError()


update_command = Update()
