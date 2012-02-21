class FSEvent(object):
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.path)


class FileCreated(FSEvent):
    pass


class FileModified(FSEvent):
    pass


class FileDeleted(FSEvent):
    pass


class FileMoved(FSEvent):

    def __init__(self, src, dst):
        self.src, self.dst = src, dst

    def __repr__(self):
        return '{}({} -> {})'.format(
                self.__class__.__name__, self.src, self.dst)


class FileCopied(FSEvent):
    pass
