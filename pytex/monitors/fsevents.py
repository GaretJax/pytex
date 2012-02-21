from __future__ import absolute_import

from operator import attrgetter

import fsevents


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


class Stream(fsevents.Stream):

    EVENT_MAPPINGS = {
        fsevents.IN_CREATE: FileCreated,
        fsevents.IN_MODIFY: FileModified,
        fsevents.IN_DELETE: FileDeleted,
        (fsevents.IN_MOVED_FROM, fsevents.IN_MOVED_TO): FileMoved,
    }

    def __init__(self, callback, path):
        self.final_callback = callback
        self.linked_events = {}
        super(Stream, self).__init__(self.handle_event, path, file_events=True)

    def handle_event(self, event):
        if event.cookie:
            events = self.linked_events.setdefault(event.cookie, [])
            events.append(event)

            if len(events) > 2:
                print repr(events)
                raise RuntimeError("More than 2 events with the same cookie!")
            elif len(events) == 2:
                # Handle multiple events
                events.sort(key=attrgetter('mask'))
                events = [(e.mask, e.name) for e in events]
                key, paths = zip(*events)
                self.final_callback(self.EVENT_MAPPINGS[key](*paths))
        else:
            # Handle single event
            self.final_callback(self.EVENT_MAPPINGS[event.mask](event.name))


class Observer(fsevents.Observer):

    def monitor(self, path, callback):
        stream = Stream(callback, path)
        super(Observer, self).schedule(stream)

    def stop(self, unschedule=True, join=True):
        if unschedule and self.streams:
            for stream in self.streams:
                self.unschedule(stream)

        super(Observer, self).stop()

        if join:
            self.join()
