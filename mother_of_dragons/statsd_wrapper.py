from statsd import StatsClient


class StatsdWrapper:
    """Simple wrapper around the statsd client."""
    statsd = None

    def __init__(self, host, port, prefix):
        if host:
            self.statsd = StatsClient(
                host=host,
                port=port,
                prefix=prefix,
            )

    def incr(self, *args):
        if self.statsd:
            self.statsd.incr(*args)

    def decr(self, *args):
        if self.statsd:
            self.statsd.decr(*args)

    def gauge(self, *args):
        if self.statsd:
            self.statsd.gauge(*args)

    def timing(self, *args):
        if self.statsd:
            self.statsd.timing(*args)

    def timer(self, *args):
        if self.statsd:
            self.statsd.timer(*args)

    def set(self, *args):
        if self.statsd:
            self.statsd.set(*args)
