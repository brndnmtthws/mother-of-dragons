"""Gevent timer."""

import gevent


class Timer:
    """A simple gevent timer class."""

    def __init__(self, func, delay):
        """Initialize the timer."""
        self.func = func
        self.delay = delay

    def start(self):
        """Start the timer."""
        gevent.sleep(self.delay)
        self.func()
