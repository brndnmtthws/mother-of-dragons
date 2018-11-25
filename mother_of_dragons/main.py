from gevent import monkey
monkey.patch_all()
import gevent
import signal
import toml
import json
from .opts import Opts
from .opts import default_config_toml


def run_forever():
    while True:
        gevent.sleep(1000)


def main():
    opts = Opts()
    gevent.signal(signal.SIGQUIT, gevent.kill)
    thread = gevent.spawn(run_forever)
    from .mother import Mother

    config = toml.loads(default_config_toml)
    if opts.args.config.endswith('json'):
        with open(opts.args.config, 'r') as f:
            config.update(json.load(f))
        print('Loaded JSON config from {}'.format(opts.args.config))
    elif opts.args.config.endswith('toml'):
        with open(opts.args.config, 'r') as f:
            config.update(toml.load(f))
        print('Loaded TOML config from {}'.format(opts.args.config))

    m = Mother(config)

    m.start()
    thread.join()
