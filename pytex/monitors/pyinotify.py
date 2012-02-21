from __future__ import absolute_import

from pytex.monitors import base
import pyinotify

from operator import attrgetter



class Stream(object):

    EVENT_MAPPINGS = {
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
            self.final_callback(self.EVENT_MAPPINGS[event.mask](event.name))


class Observer(object):

    def __init__(self):
        self.vm = pyinotify.WatchManager()
        self.notifier = pyinotify.ThreadedNotifier(self.vm)

    def start(self):
        self.notifier.start()

    def monitor(self, path, callback):
        stream = Stream(callback)
        mask = pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO | pyinotify.IN_ACCESS | pyinotify.IN_ATTRIB
        self.vm.add_watch(path, mask, stream.handle_event, rec=True)

    def stop(self):
        self.notifier.stop()
