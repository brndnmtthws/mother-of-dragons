"""There be dragon."""
from dragon_rest.dragons import DragonAPI
import statsd
import time


class Dragon:
    """Dragon handler class."""

    def __init__(self,
                 host,
                 dragon_timeout,
                 dragon_health_hashrate_min,
                 dragon_health_hashrate_duration,
                 dragon_health_reboot,
                 dragon_autotune_mode,
                 dragon_auto_upgrade,
                 pools,
                 statsd):
        """Construct a dragon (not literally tho)."""
        self.host = host
        self.dragon_timeout = dragon_timeout
        self.dragon_health_hashrate_min = dragon_health_hashrate_min
        self.dragon_health_hashrate_duration = dragon_health_hashrate_duration
        self.dragon_health_reboot = dragon_health_reboot
        self.dragon_autotune_mode = dragon_autotune_mode
        self.dragon_auto_upgrade = dragon_auto_upgrade

        self.dragon = DragonAPI(host, dragon_timeout)
        self.overview = self.dragon.overview()
        self.mac_address = self.overview['version']['ethaddr']
        self.worker = 'dragon-' + ''.join(self.mac_address.split(':'))[-8:]
        self.pools = self._assign_pools(pools)
        self.statsd = statsd
        self.statsd.incr('worker.{}.action.added'.format(self.worker))

        # Assume a dragon is initially healthy
        self.healthy_since = time.time()

        print('New dragon worker={} host={} mac_address={}'
              .format(self.worker,
                      host,
                      self.mac_address))

    def _assign_pools(self, pools):
        default_pool = []
        # look for a pool that has this mac address defined
        for pool in pools:
            if self.mac_address in pool['mac_addresses']:
                return pool['pools']
            if pool['mac_addresses'] is None \
                    or len(pool['mac_addresses']) == 0:
                default_pool = pool
        # if no pool with this mac was found, use the default pool
        return default_pool['pools']

    def check_and_update_firmware(self, firmware):
        """Check firmware version and update to latest if necessary."""
        latest_firmware = self.dragon.getLatestFirmwareVersion()
        if 'version' in latest_firmware and \
                latest_firmware['version'] != \
                latest_firmware['currentVersion']:
            print('New firmware version available for worker={},'
                  ' currentVersion={}, version={}'.format(
                      self.worker,
                      latest_firmware['currentVersion'],
                      latest_firmware['version'])
                  )
            if self.dragon_auto_upgrade:
                url = latest_firmware['url']
                local_file = firmware.get_firmware_path(url)
                print('Performing firmware upgrade for worker={} '
                      'with url={} using local_file={}'.format(self.worker,
                                                               url,
                                                               local_file))
                self.dragon.upgradeUpload(local_file)
                self.statsd.incr(
                    'worker.{}.action.upgraded'.format(self.worker))
                return True
        return False

    def check_and_update_autotune(self):
        """Check current autotune setting and update if necessary."""
        autotune = self.dragon.getAutoTune()
        if 'autoTuneMode' in autotune and \
                autotune['autoTuneMode'] != self.dragon_autotune_mode:
            print('Changing autotune setting for worker={} '
                  'from {} to {}'.format(self.worker,
                                         autotune['autoTuneMode'],
                                         self.dragon_autotune_mode))
            self.dragon.setAutoTune(self.dragon_autotune_mode)
            self.statsd.incr('worker.{}.action.autotuneChanged'
                             .format(self.worker))
            return True
        return False

    def _get_pool_for(self, idx):
        p = [x for x in self.pools if x['id'] == idx]
        if len(p) == 0:
            return {
                'url': None,
                'username': None,
                'password': None,
            }
        else:
            return p[0]

    def check_and_update_pools(self):
        """Check and update the dragon's pool configuration."""
        configured_pools = self.dragon.pools()['pools']
        if not self._pools_same(configured_pools):
            print('Pools on worker={} do not match desired state, '
                  'updating pool configuration'.format(self.worker))

            # ugly but necessary
            p1 = self._get_pool_for(0)
            pool1 = p1['url']
            username1 = '{}.{}'.format(p1['username'], self.worker)
            password1 = p1['password']

            p2 = self._get_pool_for(1)
            if p2:
                pool2 = p2['url']
                username2 = '{}.{}'.format(p2['username'], self.worker)
                password2 = p2['password']
            else:
                pool2 = username2 = password2 = None

            p3 = self._get_pool_for(2)
            if p3:
                pool3 = p3['url']
                username3 = '{}.{}'.format(p3['username'], self.worker)
                password3 = p3['password']
            else:
                pool3 = username3 = password3 = None

            self.dragon.updatePools(pool1=pool1,
                                    username1=username1,
                                    password1=password1,
                                    pool2=pool2,
                                    username2=username2,
                                    password2=password2,
                                    pool3=pool3,
                                    username3=username3,
                                    password3=password3)
            self.statsd.incr(
                'worker.{}.action.poolsChanged'.format(self.worker))
            return True
        return False

    def _pools_same(self, configured_pools):
        for idx, pool in enumerate(configured_pools):
            p = [x for x in self.pools if x['id'] == idx][0]
            if p['url'] != pool['url']:
                return False
            username = p['username'] + '.' + self.worker
            if username != pool['user']:
                return False
            if p['password'] != pool['pass']:
                return False
        return True

    def fetch_stats(self):
        """Fetch the dragon stats and optionally forward them to statsd."""
        summary = self.dragon.summary()
        print('worker={0} S0={1} T0={2}C MHs5m={3:.2f} S1={4} T1={5}C'
              ' MHs5m={6:.2f} S2={7} T2={8}C MHs5m={9:.2f}'
              .format(
                  self.worker,
                  summary['DEVS'][0]['Status'],
                  summary['DEVS'][0]['Temperature'],
                  summary['DEVS'][0]['MHS 5m'],
                  summary['DEVS'][1]['Status'],
                  summary['DEVS'][1]['Temperature'],
                  summary['DEVS'][1]['MHS 5m'],
                  summary['DEVS'][2]['Status'],
                  summary['DEVS'][2]['Temperature'],
                  summary['DEVS'][2]['MHS 5m'],
              ))
        self.statsd.gauge(
            'worker.{}.hardware.fan_duty'.format(
                self.worker),
            summary['HARDWARE']['Fan duty'])
        for dev in summary['DEVS']:
            self.statsd.gauge(
                'worker.{}.dev.{}.Alive'.format(
                    self.worker,
                    dev['ID']
                ),
                int(dev['Status'] == 'Alive'))
            metrics = [
                'Temperature',
                'MHS av',
                'MHS 5s',
                'MHS 1m',
                'MHS 5m',
                'MHS 15m',
                'Accepted',
                'Rejected',
                'Hardware Errors',
                'Utility',
                'Last Share Pool',
                'Last Share Time',
                'Total MH',
                'Diff1 Work',
                'Difficulty Accepted',
                'Difficulty Rejected',
                'Last Share Difficulty',
                'Last Valid Work',
                'Device Hardware%',
                'Device Rejected%',
                'Device Elapsed',
                'Hash Rate',
            ]
            for metric in metrics:
                self.statsd.gauge(
                    'worker.{}.dev.{}.{}'.format(
                        self.worker,
                        dev['ID'],
                        metric.replace(' ', '-').replace('%', '')
                    ),
                    dev[metric])

        for pool in summary['POOLS']:
            metrics = [
                'Getworks',
                'Accepted',
                'Rejected',
                'Works',
                'Discarded',
                'Stale',
                'Get Failures',
                'Remote Failures',
                'Last Share Time',
                'Diff1 Shares',
                'Difficulty Accepted',
                'Difficulty Rejected',
                'Difficulty Stale',
                'Last Share Difficulty',
                'Work Difficulty',
                'Stratum Difficulty',
                'Best Share',
                'Pool Rejected%',
                'Pool Stale%',
                'Bad Work',
                'Current Block Height',
                'Current Block Version',
            ]
            for metric in metrics:
                self.statsd.gauge(
                    'worker.{}.pool.{}.{}'.format(
                        self.worker,
                        pool['POOL'],
                        metric.replace(' ', '-').replace('%', '')
                    ),
                    pool[metric])
        return summary

    def check_health(self):
        """Check the health of a dragon, and optionally reboot it."""
        summary = self.dragon.summary()
        healthy = True
        below_threshhold = False

        # check each ASIC device
        for dev in summary['DEVS']:
            if dev['Status'] == 'Dead':
                print('worker={} has dead device, ID={}'
                      .format(self.worker, dev['ID']))
                healthy = False
            # check if 15m hashrate is below threshhold
            if dev['MHS 15m'] / 1000.0 < self.dragon_health_hashrate_min:
                print('worker={} 15m hashrate for dev ID={} is below '
                      'minimum threshhold of {}, current MHS 15m={}'
                      .format(
                          self.worker,
                          dev['ID'],
                          self.dragon_health_hashrate_min,
                          dev['MHS 15m']
                      ))
                below_threshhold = True

        if not below_threshhold:
            self.healthy_since = time.time()
        elif time.time() - self.healthy_since >= \
                self.dragon_health_hashrate_duration:
            healthy = False

        if not healthy:
            print('worker={} is NOT healthy'.format(self.worker))
            if self.dragon_health_reboot:
                print('Rebooting dragon worker={}'.format(self.worker))
                self.dragon.reboot()
                self.statsd.incr(
                    'worker.{}.action.rebooted'.format(self.worker))
