from __future__ import absolute_import

from operator import attrgetter

import fsevents
from pytex.monitors import base



class Stream(fsevents.Stream):

    EVENT_MAPPINGS = {
        fsevents.IN_CREATE: base.FileCreated,
        fsevents.IN_MODIFY: base.FileModified,
        fsevents.IN_DELETE: base.FileDeleted,
        (fsevents.IN_MOVED_FROM, fsevents.IN_MOVED_TO): base.FileMoved,
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
