from __future__ import absolute_import

import threading
from collections import defaultdict
from operator import attrgetter
from os.path import join

import pyinotify

from pytex.monitors import base


class Observer(threading.Thread):
    EVENT_MAPPINGS = {
        pyinotify.IN_ATTRIB: base.FileModified,
        pyinotify.IN_CREATE: base.FileCreated,
        pyinotify.IN_MODIFY: base.FileModified,
        pyinotify.IN_DELETE: base.FileDeleted,
        (pyinotify.IN_MOVED_FROM, pyinotify.IN_MOVED_TO): base.FileMoved,
    }

    def __init__(self):
        super(Observer, self).__init__()
        self.vm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.vm, timeout=10)
        self.stop_requested = False

    def monitor(self, path, callback):
        self.final_callback = callback
        self.linked_events = {}
        self.event_buffer = defaultdict(list)
        mask = 0
        mask |= pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE
        mask |= pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
        mask |= pyinotify.IN_ATTRIB
        self.vm.add_watch(path, mask, self.handle_event, rec=True)

    def run(self):
        while not self.stop_requested:
            # Process events
            self.notifier.process_events()
            while self.notifier.check_events():
                self.notifier.read_events()
                self.notifier.process_events()

            # Send callbacks for the last item of each event
            for k, v in self.event_buffer.items():
                self.final_callback(v[-1])

            self.event_buffer.clear()

    def handle_event(self, event):
        if hasattr(event, "cookie"):
            events = self.linked_events.setdefault(event.cookie, [])
            events.append(event)

            if len(events) > 2:
                print(repr(events))
                raise RuntimeError("More than 2 events with the same cookie!")
            elif len(events) == 2:
                # Handle multiple events
                events.sort(key=attrgetter("mask"))
                events = [(e.mask, join(e.path, e.name)) for e in events]
                key, paths = zip(*events)

                source = paths[0]
                target = paths[1]

                # Move the events of the moved file
                if source in self.event_buffer:
                    self.event_buffer[target] += self.event_buffer[source]
                    del self.event_buffer[source]

                self.event_buffer[target] += [self.EVENT_MAPPINGS[key](*paths)]

        else:
            # Handle single event
            try:
                event_class = self.EVENT_MAPPINGS[event.mask]
            except KeyError:
                print("Ignoring event with opflag {}".format(event.mask))
            else:
                path = join(event.path, event.name)
                self.event_buffer[path] += [event_class(path)]

    def stop(self):
        self.stop_requested = True
        self.join()
