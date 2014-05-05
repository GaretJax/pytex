from __future__ import absolute_import

from pytex.monitors import base
import pyinotify

from operator import attrgetter

import os
import threading
from collections import defaultdict


class CoalescerThread(threading.Thread):
    EVENT_MAPPINGS = {
        pyinotify.IN_ATTRIB: base.FileModified,
        pyinotify.IN_CREATE: base.FileCreated,
        pyinotify.IN_MODIFY: base.FileModified,
        pyinotify.IN_DELETE: base.FileDeleted,
        (pyinotify.IN_MOVED_FROM, pyinotify.IN_MOVED_TO): base.FileMoved,
    }

    def __init__(self):
        threading.Thread.__init__(self)
        self.vm = pyinotify.WatchManager()
        self.notifier = pyinotify.Notifier(self.vm, timeout=100)
        self.flag = False

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
        while not self.flag:
            # Process events
            self.notifier.process_events()
            while self.notifier.check_events():
                self.notifier.read_events()
                self.notifier.process_events()

            # Send callbacks for the last item of each event
            for k, v in self.event_buffer.iteritems():
                self.final_callback(v[-1])

            self.event_buffer.clear()

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
                for e in self.EVENT_MAPPINGS[key](*paths):
                    self.event_buffer[e.path] += [e]
        else:
            # Handle single event
            try:
                event_class = self.EVENT_MAPPINGS[event.mask]
            except KeyError:
                print 'Ignoring event with opflag {}'.format(event.mask)
            else:
                path = os.path.join(event.path, event.name)
                self.event_buffer[path] += [event_class(path)]

    def stop(self):
        self.flag = True
        self.join()


class Observer(object):
    def __init__(self):
        self.coalescer = CoalescerThread()

    def start(self):
        self.coalescer.start()

    def monitor(self, path, callback):
        self.coalescer.monitor(path, callback)

    def stop(self):
        self.coalescer.stop()
