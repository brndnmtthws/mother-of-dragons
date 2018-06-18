"""Command line options."""

import argparse

default_pool_json = """
[
   {
      "mac_addresses":[],
      "pools":[
         {
            "id":0,
            "url":"stratum+tcp://us-east.stratum.slushpool.com:3333",
            "username":"brndnmtthws",
            "password":"x"
         },
         {
            "id":1,
            "url":"stratum+tcp://pool.ckpool.org:3333",
            "username":"3GWdXx9dfLPvSe7d8UnxjnDnSAJodTTbrt",
            "password":"x"
         }
      ]
   }
]
"""


class Opts:
    """Parse command line options."""

    def __init__(self):
        """Parse and initialize the options."""
        parser = argparse.ArgumentParser(description='Management tool for '
                                         'DragonMint T1.',
                                         formatter_class=argparse.
                                         ArgumentDefaultsHelpFormatter)

        parser.add_argument('--network', type=str,
                            help='Local network in CIDR notation',
                            default="10.1.0.0/22")
        parser.add_argument('--scan-interval', type=int,
                            help='Local networking scanning interval',
                            default=300)
        parser.add_argument('--scan-timeout', type=int,
                            help='Local networking scanning timeout per host',
                            default=10)
        parser.add_argument('--dragon-timeout', type=int,
                            help='Timeout for individual dragon API calls',
                            default=10)
        parser.add_argument('--dragon-health-hashrate-min', type=int,
                            help='Minimum hashrate in GH/s (per device) that '
                            'is considered healthy, based on the 15m '
                            'hashrate as reported by the dragon.',
                            default=1000)
        parser.add_argument('--dragon-health-hashrate-duration', type=int,
                            help='Amount of time (in seconds) that the '
                            'hashrate (per device) must be below the minimum '
                            'threshhold for it to be considered unhealthy.',
                            default=3600)
        parser.add_argument('--dragon-health-reboot',
                            help='Enable automatic rebooting of unhealthy '
                            'dragons. A dragon is considered unhealthy if '
                            'a device is marked as dead or the hashrate '
                            'has been below the minimum healthy threshhold '
                            'for more than the duration specified.',
                            action='store_true')
        parser.add_argument('--dragon-health-check-interval',
                            help='Health checking interval in seconds',
                            type=int, default=300)
        parser.add_argument('--dragon-autotune-mode', type=str,
                            help='Desired autotune mode of each dragon.'
                            'Should be one of: ["efficient","balanced",'
                            '"factory","performance"].',
                            default='balanced')
        parser.add_argument('--dragon-auto-upgrade',
                            help='Automatically upgrade dragons to '
                            'latest firmware.',
                            action='store_true')
        parser.add_argument('--pools',
                            help='A JSON blob specifying the pool '
                            'configuration for dragons. To apply a pool '
                            'config to a specific set of dragons, specify '
                            'the "mac_addresses" parameter accordingly.',
                            default=default_pool_json)
        parser.add_argument('--statsd-host',
                            help='statsd host to enable statsd metrics',
                            type=str, default=None)
        parser.add_argument('--statsd-port',
                            help='statsd port',
                            type=int, default=8125)
        parser.add_argument('--statsd-prefix',
                            help='statsd prefix',
                            type=str, default='dragons')
        parser.add_argument('--statsd-interval',
                            help='Interval in seconds for fetching metrics '
                            'and forwarding them to statsd from each dragon',
                            type=int, default=60)
        parser.add_argument('--firmwares-path',
                            help='Local path for caching firmware files used '
                            'during upgrades',
                            type=str, default='firmwares/')

        self.args = parser.parse_args()
