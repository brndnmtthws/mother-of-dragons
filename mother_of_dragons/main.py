from gevent import monkey
monkey.patch_all()
import gevent
import signal
from .opts import Opts


def run_forever():
    while True:
        gevent.sleep(1000)


def main():
    opts = Opts()
    gevent.signal(signal.SIGQUIT, gevent.kill)
    thread = gevent.spawn(run_forever)
    from .mother import Mother
    m = Mother(opts.args.network,
               scan_timeout=opts.args.scan_timeout,
               scan_interval=opts.args.scan_interval,
               dragon_timeout=opts.args.dragon_timeout,
               dragon_health_hashrate_min=opts.args.dragon_health_hashrate_min,
               dragon_health_hashrate_duration=
               opts.args.dragon_health_hashrate_duration,
               dragon_health_reboot=opts.args.dragon_health_reboot,
               dragon_health_check_interval=
               opts.args.dragon_health_check_interval,
               dragon_autotune_mode=opts.args.dragon_autotune_mode,
               dragon_auto_upgrade=opts.args.dragon_auto_upgrade,
               pools=opts.args.pools,
               statsd_host=opts.args.statsd_host,
               statsd_port=opts.args.statsd_port,
               statsd_prefix=opts.args.statsd_prefix,
               statsd_interval=opts.args.statsd_interval,
               firmwares_path=opts.args.firmwares_path)

    m.start()
    thread.join()
