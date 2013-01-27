import contextlib
import os
import subprocess


class VersionControlProvider(object):

    def __init__(self, logger, path=None):
        if path is None:
            path = os.getcwd()
        self.path = path
        self.logger = logger

    @contextlib.contextmanager
    def cdrootdir(self):
        curdir = rootdir = os.getcwd()

        if self.path.startswith(rootdir):
            curdir = rootdir = self.path

        while not self.isrootdir(rootdir):
            rootdir = os.path.dirname(rootdir)

        os.chdir(rootdir)

        try:
            yield
        finally:
            os.chdir(curdir)

    def runcmd(self, *args, **kwargs):
        try:
            return subprocess.check_output(args, **kwargs)
        except subprocess.CalledProcessError as e:
            self.logger.error(e.output)
            self.logger.error(e)

    def isrootdir(self, path):
        raise NotImplementedError

    def init(self):
        raise NotImplementedError()

    def tag(self, name, message):
        raise NotImplementedError()
