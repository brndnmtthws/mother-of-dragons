"""There be dragon."""
from dragon_rest.dragons import DragonAPI
import statsd
import time
import serpy


class Dragon(object):
    """Dragon handler class."""

    def __init__(self,
                 host,
                 api_timeout,
                 credentials,
                 configs,
                 statsd):
        """Construct a dragon (not literally tho)."""
        self.ip_address = self.host = host

        self.dragon = None
        for cred in credentials:
            try:
                self.dragon = DragonAPI(host,
                                        username=cred['username'],
                                        password=cred['password'],
                                        timeout=api_timeout)
                self.overview = self.dragon.overview()
                break
            except:
                pass

        if self.dragon is None:
            raise Exception("Exhausted all credentials, unable to add dragon"
                            "with host={}".format(host))

        self.type = self.overview['type']
        self.mac_address = self.overview['version']['ethaddr']

        self.config = self.get_config_for_this_dragon(configs)

        self.api_timeout = api_timeout
        self.health_hashrate_duration = self.config['health_hashrate_duration']
        self.health_hashrate_min = self.config['health_hashrate_minimum']
        self.health_check_interval = self.config['health_check_interval']
        self.health_reboot = self.config['health_reboot']
        self.autotune_mode = self.config['autotune_mode']
        self.autotune_level = self.config['autotune_level']
        self.auto_upgrade = self.config['auto_upgrade']

        self.worker = 'dragon-' + ''.join(self.mac_address.split(':'))[-8:]
        self.statsd = statsd
        self.statsd.incr('worker.{}.{}.action.added'.format(
            self.type, self.worker))
        self.rebooted = False

        # Assume a dragon is initially healthy
        self.healthy_since = time.time()

        print('New dragon worker={} host={} mac_address={}'
              .format(self.worker,
                      host,
                      self.mac_address))

    def get_config_for_this_dragon(self, configs):
        # Condition 1: find config where both model and MAC matches
        for c in configs:
            if 'apply_to' in c and \
                'models' in c['apply_to'] and \
                self.type in c['apply_to']['models'] and \
                'mac_addresses' in c and \
                    self.mac_address in c['apply_to']['mac_addresses']:
                return c

        # Condition 2: model is specified, but MAC is not
        for c in configs:
            if 'apply_to' in c and \
                'models' in c['apply_to'] and \
                self.type in c['apply_to']['models'] and \
                    ('mac_addresses' not in c or len(c['apply_to']['mac_addresses']) == 0):
                return c

        # Condition 3: MAC is specified, but model is not
        for c in configs:
            if 'apply_to' in c and \
                'mac_addresses' in c['apply_to'] and \
                self.mac_address in c['apply_to']['mac_addresses'] and \
                    ('models' not in c or len(c['apply_to']['models']) == 0):
                return c

        # Condition 4: fallback to first default config
        for c in configs:
            if 'apply_to' not in c or \
                    (
                        ('models' not in c or len(c['apply_to']['models']) == 0) and
                        ('mac_addresses' not in c or len(
                            c['apply_to']['mac_addresses']) == 0)
                    ):
                return c

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
            if self.auto_upgrade:
                url = latest_firmware['url']
                local_file = firmware.get_firmware_path(url)
                print('Performing firmware upgrade for worker={} '
                      'with url={} using local_file={}'.format(self.worker,
                                                               url,
                                                               local_file))
                self.dragon.upgradeUpload(local_file)
                self.statsd.incr(
                    'worker.{}.{}.action.upgraded'.format(self.type, self.worker))
                return True
        return False

    def check_and_update_autotune(self):
        """Check current autotune setting and update if necessary."""
        autotune = self.dragon.getAutoTune()
        if 'autoTuneMode' in autotune:
            if 'mode' in autotune['autoTuneMode'] and 'level' in autotune['autoTuneMode']:
                if autotune['autoTuneMode']['mode'] != self.autotune_mode:
                    print('Changing autotune setting for worker={} '
                          'from {} to mode={} level={}'.format(self.worker,
                                                               autotune['autoTuneMode'],
                                                               self.autotune_mode,
                                                               self.autotune_level))
                    self.dragon.setAutoTune(
                        self.autotune_mode, self.autotune_level)
                    self.statsd.incr('worker.{}.{}.action.autotuneChanged'
                                     .format(self.type, self.worker))
                    return True
            elif autotune['autoTuneMode'] != self.autotune_mode:
                print('Changing autotune setting for worker={} '
                      'from {} to {}'.format(self.worker,
                                             autotune['autoTuneMode'],
                                             self.autotune_mode))
                self.dragon.setAutoTune(self.autotune_mode)
                self.statsd.incr('worker.{}.{}.action.autotuneChanged'
                                 .format(self.type, self.worker))
                return True
        return False

    def _get_pool_for(self, idx):
        if idx > len(self.config['pools']) - 1:
            return {
                'url': None,
                'username': None,
                'password': None,
            }
        else:
            return self.config['pools'][idx]

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
                'worker.{}.{}.action.poolsChanged'.format(self.type, self.worker))
            return True
        return False

    def _pools_same(self, configured_pools):
        for idx, pool in enumerate(configured_pools):
            p = self._get_pool_for(idx)
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
        self.summary = summary = self.dragon.summary()
        if 'DEVS' in summary:
            summary_out = 'worker={0}'.format(self.worker)
            for idx, stats in enumerate(summary['DEVS']):
                summary_out += ' S{0}={1} T{0}={2}C MHs5m={3:.2f}'\
                    .format(idx,
                            stats['Status'],
                            stats['Temperature'],
                            stats['MHS 5m'])
            print(summary_out)
            if len(summary['DEVS']) != 3:
                print('Unexpected length of device summary from worker={}, length={} expected 3'
                      .format(self.worker, len(summary['DEVS'])))
        elif 'DEVS' not in summary:
            print('Device summary from worker={} not present (did it just start up?)'
                  .format(self.worker))
        self.statsd.gauge(
            'worker.{}.{}.hardware.fan_duty'.format(
                self.type,
                self.worker),
            summary['HARDWARE']['Fan duty'])
        for dev in summary['DEVS']:
            self.statsd.gauge(
                'worker.{}.{}.dev.{}.Alive'.format(
                    self.type,
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
                'Hash Rate H',
            ]
            for metric in metrics:
                if metric in dev:
                    self.statsd.gauge(
                        'worker.{}.{}.dev.{}.{}'.format(
                            self.type,
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
                if metric in pool:
                    self.statsd.gauge(
                        'worker.{}.{}.pool.{}.{}'.format(
                            self.type,
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
        temperature_wtf = False

        # check each ASIC device
        for dev in summary['DEVS']:
            if dev['Status'] == 'Dead':
                print('worker={} has dead device, ID={}'
                      .format(self.worker, dev['ID']))
                healthy = False
            # check if 15m hashrate is below threshhold
            if dev['MHS 15m'] < self.health_hashrate_min:
                print('worker={} 15m hashrate for dev ID={} is below '
                      'minimum threshhold of {}, current MHS 15m={}'
                      .format(
                          self.worker,
                          dev['ID'],
                          self.health_hashrate_min,
                          dev['MHS 15m']
                      ))
                below_threshhold = True
            if dev['Temperature'] > 200:
                temperature_wtf = True
                print('worker={} showing temp of {} for dev ID={}, '
                      'may be unhealthy'.format(
                          self.worker,
                          dev['Temperature'],
                          dev['ID']
                      ))
        if len(summary['DEVS']) != 3:
            print('worker={} only has {} devices'.format(
                self.worker, len(summary['DEVS'])))
            below_threshhold = True

        if not below_threshhold and not temperature_wtf:
            self.healthy_since = time.time()
        elif time.time() - self.healthy_since >= \
                self.health_hashrate_duration:
            healthy = False

        if not healthy:
            print('worker={} is NOT healthy'.format(self.worker))
            if self.health_reboot:
                print('Rebooting dragon worker={}'.format(self.worker))
                self.rebooted = True
                self.dragon.reboot()
                self.statsd.incr(
                    'worker.{}.{}.action.rebooted'.format(self.type, self.worker))


class DragonSerializer(serpy.Serializer):
    """Dragon serilizer."""

    ip_address = serpy.Field()
    worker = serpy.Field()
    mac_address = serpy.Field()
    overview = serpy.Field()
