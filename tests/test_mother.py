import vcr
from pytest import fixture
from mother_of_dragons.mother import Mother
from mother_of_dragons.dragons import Dragon
from dragon_rest.dragons import DragonAPI
import gevent
import json
import tempfile
import os
from statsd import StatsClient

vcr = vcr.VCR(
    cassette_library_dir='tests/fixtures/cassettes',
    record_mode='new_episodes',
)

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

pool_json_alternate = """
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
   },
   {
      "mac_addresses":["a0:b0:45:00:e3:ab"],
      "pools":[
         {
            "id":0,
            "url":"stratum+tcp://us-east.stratum.slushpool.com:3333",
            "username":"brndnmtthws",
            "password":"lol"
         },
         {
            "id":1,
            "url":"stratum+tcp://pool.ckpool.org:3333",
            "username":"3GWdXx9dfLPvSe7d8UnxjnDnSAJodTTbrt",
            "password":"lol"
         }
      ]
   }
]
"""


@fixture
def mother():
    return Mother(network='10.1.0.0/28',
                  scan_timeout=1,
                  scan_interval=2,
                  dragon_timeout=1,
                  dragon_health_hashrate_min=1000,
                  dragon_health_hashrate_duration=3600,
                  dragon_health_reboot=True,
                  dragon_health_check_interval=60,
                  dragon_autotune_mode='balanced',
                  dragon_auto_upgrade=True,
                  pools=default_pool_json,
                  statsd_host=None,
                  statsd_port=8125,
                  statsd_prefix='dragons',
                  statsd_interval=60,
                  firmwares_path=os.path.join(tempfile.gettempdir(),
                                              'mod_test'))


@fixture
def host():
    # default host
    return '10.1.0.8'


@vcr.use_cassette()
def test_mother_scan(mother, host):
    mother.scan(schedule=False)
    gevent.sleep(5)

    assert len(mother.dragons) == 2
    assert mother.dragons[host].host == host


@vcr.use_cassette()
def test_mother_workers_started(mother, host, mocker):
    mother.dragons = {}
    mocker.patch.object(Mother, '_schedule_scanner', autospec=True)
    mocker.patch.object(Mother, '_schedule_check_health', autospec=True)
    mocker.patch.object(Mother, '_schedule_fetch_stats', autospec=True)
    mocker.patch.object(Mother, '_schedule_next_firmware_check', autospec=True)
    mother.start()
    gevent.sleep(5)

    assert len(mother.dragons) == 2

    Mother._schedule_scanner.assert_called_once_with(mother)
    Mother._schedule_check_health.assert_called()
    Mother._schedule_fetch_stats.assert_called()
    Mother._schedule_next_firmware_check.assert_called()


# @vcr.use_cassette()
# def test_mother_scan_alt(host):
#     mother = Mother(network='10.1.0.0/28',
#                       scan_timeout=1,
#                       scan_interval=2,
#                       dragon_timeout=1,
#                       dragon_health_hashrate_min=1000,
#                       dragon_health_hashrate_duration=3600,
#                       dragon_health_reboot=True,
#                       dragon_autotune_mode='balanced',
#                       dragon_auto_upgrade=True,
#                       pools=pool_json_alternate)
#     mother.scan(schedule=False)
#     gevent.sleep(5)
#
#     assert len(mother.dragons) == 2
#     assert mother.dragons[host].host == host
#     assert mother.dragons[host].pools[0]['password'] == 'lol'
#     assert mother.dragons[host].pools[1]['password'] == 'lol'

@vcr.use_cassette()
def test_fetch_stats(host):
    dragon = Dragon(host,
                    dragon_timeout=1,
                    dragon_health_hashrate_min=1000,
                    dragon_health_hashrate_duration=3600,
                    dragon_health_reboot=True,
                    dragon_autotune_mode='balanced',
                    dragon_auto_upgrade=True,
                    pools=json.loads(default_pool_json),
                    statsd=StatsClient(
                        host='127.0.0.1',
                        prefix='dragon'
                    ))
    summary = dragon.fetch_stats()

    assert len(summary['DEVS']) == 3


@vcr.use_cassette()
def test_check_health(host):
    dragon = Dragon(host,
                    dragon_timeout=1,
                    dragon_health_hashrate_min=1000,
                    dragon_health_hashrate_duration=3600,
                    dragon_health_reboot=True,
                    dragon_autotune_mode='balanced',
                    dragon_auto_upgrade=True,
                    pools=json.loads(default_pool_json),
                    statsd=StatsClient(
                        host='127.0.0.1',
                        prefix='dragon'
                    ))
    dragon.check_health()


@vcr.use_cassette()
def test_check_unhealthy_dead(host, mocker):
    mocker.patch.object(DragonAPI, 'reboot', autospec=True)
    dragon = Dragon(host,
                    dragon_timeout=1,
                    dragon_health_hashrate_min=1000,
                    dragon_health_hashrate_duration=3600,
                    dragon_health_reboot=True,
                    dragon_autotune_mode='balanced',
                    dragon_auto_upgrade=True,
                    pools=json.loads(default_pool_json),
                    statsd=StatsClient(
                        host='127.0.0.1',
                        prefix='dragon'
                    ))
    dragon.check_health()

    DragonAPI.reboot.assert_called_once_with(dragon.dragon)


@vcr.use_cassette()
def test_check_unhealthy_low_hashrate(host, mocker):
    mocker.patch.object(DragonAPI, 'reboot', autospec=True)
    dragon = Dragon(host,
                    dragon_timeout=1,
                    dragon_health_hashrate_min=1000,
                    dragon_health_hashrate_duration=0,
                    dragon_health_reboot=True,
                    dragon_autotune_mode='balanced',
                    dragon_auto_upgrade=True,
                    pools=json.loads(default_pool_json),
                    statsd=StatsClient(
                        host='127.0.0.1',
                        prefix='dragon'
                    ))
    dragon.check_health()

    DragonAPI.reboot.assert_called_once_with(dragon.dragon)
