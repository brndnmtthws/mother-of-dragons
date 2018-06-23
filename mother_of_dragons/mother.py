"""Dragon Mother."""
from dragon_rest.dragons import DragonAPI
import ipaddress
import gevent
import time
import traceback
import json
import sys
import random
from .dragons import Dragon, DragonSerializer
from .firmware import Firmware
from .timer import Timer
from .statsd_wrapper import StatsdWrapper


class Mother:
    """Interface for mother_of_dragons."""

    dragons = {}

    def __init__(self,
                 network,
                 scan_timeout,
                 scan_interval,
                 dragon_timeout,
                 dragon_health_hashrate_min,
                 dragon_health_hashrate_duration,
                 dragon_health_reboot,
                 dragon_health_check_interval,
                 dragon_autotune_mode,
                 dragon_auto_upgrade,
                 pools,
                 statsd_host,
                 statsd_port,
                 statsd_prefix,
                 statsd_interval,
                 firmwares_path,
                 inventory_file):
        """Construct a new dragon manager."""
        self.network = network
        self.scan_timeout = scan_timeout
        self.scan_interval = scan_interval
        self.dragon_timeout = dragon_timeout
        self.dragon_health_hashrate_min = dragon_health_hashrate_min
        self.dragon_health_hashrate_duration = dragon_health_hashrate_duration
        self.dragon_health_reboot = dragon_health_reboot
        self.dragon_health_check_interval = dragon_health_check_interval
        self.dragon_autotune_mode = dragon_autotune_mode
        self.dragon_auto_upgrade = dragon_auto_upgrade
        self.pools = json.loads(pools)
        self.statsd = StatsdWrapper(
            host=statsd_host,
            port=statsd_port,
            prefix=statsd_prefix,
        )
        self.statsd_interval = statsd_interval
        self.firmware = Firmware(firmwares_path)
        self.inventory_file = inventory_file

    def start(self):
        """Start the main loop of the dragon manager."""
        self.scan()

    @staticmethod
    def _is_dragon(host, timeout):
        if DragonAPI.is_dragon(host, timeout):
            return host
        return None

    def scan(self, schedule=True):
        """Scan the network for dragons."""
        print("Starting scan for dragons...")
        sys.stdout.flush()
        started_at = time.time()
        jobs = [gevent.spawn(self._is_dragon,
                             host,
                             self.scan_timeout / 2)
                for host in ipaddress.ip_network(self.network).hosts()]
        gevent.joinall(jobs, timeout=self.scan_timeout * 2)
        scan_result = [str(job.value) for job in jobs if job.value]
        timed = time.time() - started_at
        print("Scan complete, took {0:.2f}s, found {1} dragons"
              .format(timed, len(scan_result)))
        sys.stdout.flush()
        self.statsd.timing('manager.scan_timed', timed * 1000)
        self.statsd.gauge('manager.scan.count', len(scan_result))
        if schedule:
            # schedule next scan run
            self._schedule_scanner()
        # handle the results from the scan
        self._process_scan_result(set(scan_result))

    def _schedule_scanner(self):
        timer = Timer(lambda: self.scan(), self.scan_interval)
        gevent.spawn(timer.start)

    def _process_scan_result(self, scan_result):
        for host in scan_result:
            if host not in self.dragons:
                gevent.spawn(self._add_dragon, host)
        for host in self.dragons:
            if host not in scan_result:
                gevent.spawn(self._remove_dragon, host)

    def _add_dragon(self, host):
        print('Adding new dragon, host={}'.format(host))
        try:
            dragon = Dragon(host,
                            self.dragon_timeout,
                            self.dragon_health_hashrate_min,
                            self.dragon_health_hashrate_duration,
                            self.dragon_health_reboot,
                            self.dragon_autotune_mode,
                            self.dragon_auto_upgrade,
                            self.pools,
                            self.statsd)
            if not dragon.check_and_update_pools():
                if not dragon.check_and_update_autotune():
                    self.dragons[host] = dragon
                    self.fetch_stats_for_dragon(host)
                    self.check_health_of_dragon(host)
                    self.check_firmware_version(host)
            self._update_inventory()
        except Exception as e:
            self.statsd.incr('manager.dragons.exception')
            self.statsd.incr('manager.dragons.add_exception')
            print('Caught exception when adding new dragon:', e)
            traceback.print_exc()
            sys.stderr.flush()
        self.statsd.gauge('manager.dragons.count', len(self.dragons))
        self.statsd.incr('manager.dragons.added')
        sys.stdout.flush()

    def _remove_dragon(self, host):
        print('Removing dragon, host={}'.format(host))
        del self.dragons[host]
        self._update_inventory()
        self.statsd.gauge('manager.dragons.count', len(self.dragons))
        self.statsd.incr('manager.dragons.removed')
        sys.stdout.flush()

    def _update_inventory(self):
        data = [DragonSerializer(dragon).data
                for dragon in self.dragons.values()]
        with open(self.inventory_file, 'w') as outfile:
            json.dump(data, outfile, sort_keys=True, indent=2)

    def _schedule_fetch_stats(self, host):
        timer = Timer(lambda: self.fetch_stats_for_dragon(host),
                      self.statsd_interval)
        gevent.spawn(timer.start)

    def fetch_stats_for_dragon(self, host):
        """Fetch stats for a dragon and schedule the next fetch."""
        if host in self.dragons:
            try:
                self.dragons[host].fetch_stats()
                self._schedule_fetch_stats(host)
            except Exception as e:
                self.statsd.incr('manager.dragons.exception')
                self.statsd.incr('manager.dragons.stats_exception')
                print('Caught exception fetching stats of host={}'
                      ', removing dragon: {}'.format(host, str(e)))
                traceback.print_exc()
                sys.stderr.flush()
                self._remove_dragon(host)

    def _schedule_check_health(self, host):
        timer = Timer(lambda: self.check_health_of_dragon(host),
                      self.dragon_health_check_interval)
        gevent.spawn(timer.start)

    def check_health_of_dragon(self, host):
        """Check the health of a dragon and schedule the next check."""
        if host in self.dragons:
            dragon = self.dragons[host]
            try:
                dragon.check_health()
                self._schedule_check_health(host)
            except Exception as e:
                self.statsd.incr('manager.dragons.exception')
                self.statsd.incr('manager.dragons.health_exception')
                print('Caught exception checking health of host={}'
                      ', removing dragon: {}'.format(host, str(e)))
                traceback.print_exc()
                sys.stderr.flush()
                self._remove_dragon(host)

    def _schedule_next_firmware_check(self, host):
        # check approx. every 24h, +/- 24h splay
        timer = Timer(lambda: self.check_firmware_version(host),
                      24 * 3600 + (random.randint(0, 24 * 3600)))
        gevent.spawn(timer.start)

    def check_firmware_version(self, host):
        """Check the firmware of a dragon and schedule the next check."""
        if host in self.dragons:
            dragon = self.dragons[host]
            try:
                if dragon.check_and_update_firmware(self.firmware):
                    # firmware being updated, remove the dragon
                    # while it does its thing.
                    self._remove_dragon(host)
                else:
                    self._schedule_next_firmware_check(host)
            except Exception as e:
                self.statsd.incr('manager.dragons.exception')
                self.statsd.incr('manager.dragons.firmware_check_exception')
                print('Caught exception checking firmware of host={}'
                      ', removing dragon: {}'.format(host, str(e)))
                traceback.print_exc()
                sys.stderr.flush()
                self._remove_dragon(host)
