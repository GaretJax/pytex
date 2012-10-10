import os
import pipes

from pytex.versioning.base import VersionControlProvider


class Tag(object):
    # TODO: Make this extend from a generic tag

    def __init__(self, versions, name, message=None):
        self.versions = versions
        self.name = name
        self.message = message

    def __str__(self):
        return 'Tag: {}'.format(self.name)


class VersionControl(VersionControlProvider):

    def init(self):
        self.runcmd('git', 'init', self.path)
        self.logger.info('Version control (GIT) correctly initialized')

        return self

    def ignore(self, *paths):
        paths = (p + '\n' for p in paths)
        with self.cdrootdir():
            with open('.gitignore', 'a') as fh:
                fh.writelines(paths)

    def isrootdir(self, path):
        return os.path.exists(os.path.join(path, '.git'))

    def addall(self):
        with self.cdrootdir():
            self.runcmd('git', 'add', '*')

        return self

    def commit(self, message):
        self.runcmd('git', 'commit', '-m', message)
        self.logger.info('Commit created')

        return self

    def tag(self, name, message):
        self.runcmd('git', 'tag', '-a', name, '-m', message)
        self.logger.info('Tag {!r} created'.format(name))
        #http://learn.github.com/p/tagging.html

        return self

    def export_tag(self, tag, dest):
        # TODO: Make this bullet proof (and secure...)
        base = os.path.dirname(dest)
        if not os.path.exists(base):
            os.makedirs(base)
        prefix = os.path.join(os.path.basename(dest), '')
        cmd = 'git archive --prefix={} {} | (cd {} ; tar x)'
        cmd = cmd.format(
            pipes.quote(prefix),
            pipes.quote(tag),
            pipes.quote(base)
        )

        with self.cdrootdir():
            self.runcmd(cmd, shell=True)

        return self

    def get_tags(self):
        lines = self.runcmd('git', 'tag', '-l', '-n1').splitlines()

        tags = []

        for line in lines:
            name, message = line.split(' ', 1)
            message = message.strip()
            tag = Tag(self, name, message)
            tags.append(tag)

        return tags
