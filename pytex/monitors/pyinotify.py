from __future__ import absolute_import

from pytex.monitors import base
import pyinotify

from operator import attrgetter

import os

class Stream(object):

    EVENT_MAPPINGS = {
# TODO: The following OP flags are not yet defined. Do we need them?
#       pyinotify.IN_ACCESS        : 0x00000001,  # File was accessed
#       pyinotify.IN_CLOSE_WRITE   : 0x00000008,  # Writable file was closed
#       pyinotify.IN_CLOSE_NOWRITE : 0x00000010,  # Unwritable file closed
#       pyinotify.IN_OPEN          : 0x00000020,  # File was opened
#       pyinotify.IN_DELETE_SELF   : 0x00000400,  # Self (watched item itself) was deleted
#       pyinotify.IN_MOVE_SELF     : 0x00000800,  # Self (watched item itself) was moved
        pyinotify.IN_ATTRIB: base.FileModified,
        pyinotify.IN_CREATE: base.FileCreated,
        pyinotify.IN_MODIFY: base.FileModified,
        pyinotify.IN_DELETE: base.FileDeleted,
        (pyinotify.IN_MOVED_FROM, pyinotify.IN_MOVED_TO): base.FileMoved,
    }

    def __init__(self, callback):
        self.final_callback = callback
        self.linked_events = {}

    def handle_event(self, event):
        if hasattr(event, 'cookie'):
            events = self.linked_events.setdefault(event.cookie, [])
            events.append(event)

            if len(events) > 2:
                print repr(events)
                raise RuntimeError("More than 2 events with the same cookie!")
            elif len(events) == 2:
                # Handle multiple events
                events.sort(key=attrgetter('mask'))
                events = [(e.mask, e.path) for e in events]
                key, paths = zip(*events)
                self.final_callback(self.EVENT_MAPPINGS[key](*paths))
        else:
            # Handle single event
            try:
                event_class = self.EVENT_MAPPINGS[event.mask]
            except KeyError:
                print 'Ignoring event with opflag {}'.format(event.mask)
            else:
                self.final_callback(event_class(os.path.join(event.path, event.name)))


class Observer(object):

    def __init__(self):
        self.vm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.vm)

    def start(self):
        self.notifier.start()

    def monitor(self, path, callback):
        stream = Stream(callback)
        mask = 0
        mask |= pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE
        mask |= pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
        mask |= pyinotify.IN_ATTRIB
        self.vm.add_watch(path, mask, stream.handle_event, rec=True)

    def stop(self):
        self.notifier.stop()
