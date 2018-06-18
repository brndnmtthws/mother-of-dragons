[![Build Status](https://travis-ci.org/brndnmtthws/mother-of-dragons.svg?branch=master)](https://travis-ci.org/brndnmtthws/mother-of-dragons) [![Maintainability](https://api.codeclimate.com/v1/badges/b555c676a4940731d47f/maintainability)](https://codeclimate.com/github/brndnmtthws/mother-of-dragons/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/b555c676a4940731d47f/test_coverage)](https://codeclimate.com/github/brndnmtthws/mother-of-dragons/test_coverage) [![PyPI version](https://badge.fury.io/py/mother-of-dragons.svg)](https://badge.fury.io/py/mother-of-dragons)
# 🐲👸🔥🐉 Mother of Dragons 🐲👸🔥🐉
*Be smart. Be mother. Be Mother of Dragons.*

DragonMint T1 or B29 management tool based on
[dragon-rest](https://github.com/brndnmtthws/dragon-rest)

![Mom with dragons](/mom.gif?raw=true)

## Features

**Mother of Dragons** can:
 * Auto-detect new dragons on your local network and configure them
 * Collect metrics from dragons and forward them to statsd
 * Automatically update to the latest firmware version when new miners are
   added
 * Keep your dragons happy and healthy by rebooting them when they’re sick
 * Apply different pool configurations to different dragons based on their
   MAC address
 * Free you up from having to manually manage your dragons so you can go
   vacation like a movie star 😎

## How it works

When you run mother-of-dragons, it will start 3 separate closed loops:
 * **Scan loop**: scans the local network at a specified interval
   (`--scan-interval`) looking for dragons. It checks for the dragons by
   making an HTTP request and checking the result. The scan only works if
   your local network allows traffic on port 80 to all the specified IPs,
   which you define with the `--network` parameter.

   * When a new dragon is found, the dragon will be configured with the desired
     pool and autotune. If you specify a pool configuration with a MAC address, mother will assign the pool config with the matching address.

   * If `--dragon-auto-upgrade` is set, dragons will be updated to the latest
     firmware version when added.

 * **Metrics loop**: fetches metrics from every known dragon according to
   `--statsd-interval` and forwards those metrics to statsd provided you
   have configured `--statsd-host`.

 * **Health loop**: checks each dragon according to the specified interval
   `--dragon-health-check-interval` and may (optionally) reboot a dragon if:

   * The dragon has 1 or more devices (ASIC boards) marked as 'Dead'.

   * The dragon has 1 or more devices which have been below
     `--dragon-health-hashrate-min` for at least
     `--dragon-health-hashrate-duration`.

## Super Quickstart

```
$ pip install mother-of-dragons
$ mother-of-dragons --help
...
$ mother-of-dragons --network='10.1.0.0/22' # specify your local network
```

Be sure to change the `--pools` configuration unless you want to mine
for me 😛

## Configuration


```
usage: mother-of-dragons [-h] [--network NETWORK] [--scan-interval SCAN_INTERVAL]
                    [--scan-timeout SCAN_TIMEOUT]
                    [--dragon-timeout DRAGON_TIMEOUT]
                    [--dragon-health-hashrate-min DRAGON_HEALTH_HASHRATE_MIN]
                    [--dragon-health-hashrate-duration DRAGON_HEALTH_HASHRATE_DURATION]
                    [--dragon-health-reboot]
                    [--dragon-health-check-interval DRAGON_HEALTH_CHECK_INTERVAL]
                    [--dragon-autotune-mode DRAGON_AUTOTUNE_MODE]
                    [--dragon-auto-upgrade] [--pools POOLS]
                    [--statsd-host STATSD_HOST] [--statsd-port STATSD_PORT]
                    [--statsd-prefix STATSD_PREFIX]
                    [--statsd-interval STATSD_INTERVAL]

Management tool for DragonMint T1.

optional arguments:
-h, --help            show this help message and exit
--network NETWORK     Local network in CIDR notation (default: 10.1.0.0/22)
--scan-interval SCAN_INTERVAL
                      Local networking scanning interval (default: 300)
--scan-timeout SCAN_TIMEOUT
                      Local networking scanning timeout per host (default:
                      10)
--dragon-timeout DRAGON_TIMEOUT
                      Timeout for individual dragon API calls (default: 10)
--dragon-health-hashrate-min DRAGON_HEALTH_HASHRATE_MIN
                      Minimum hashrate in GH/s (per device) that is
                      considered healthy, based on the 15m hashrate as
                      reported by the dragon. (default: 1000)
--dragon-health-hashrate-duration DRAGON_HEALTH_HASHRATE_DURATION
                      Amount of time (in seconds) that the hashrate (per
                      device) must be below the minimum threshhold for it to
                      be considered unhealthy. (default: 3600)
--dragon-health-reboot
                      Enable automatic rebooting of unhealthy dragons. A
                      dragon is considered unhealthy if a device is marked
                      as dead or the hashrate has been below the minimum
                      healthy threshhold for more than the duration
                      specified. (default: False)
--dragon-health-check-interval DRAGON_HEALTH_CHECK_INTERVAL
                      Health checking interval in seconds (default: 300)
--dragon-autotune-mode DRAGON_AUTOTUNE_MODE
                      Desired autotune mode of each dragon.Should be one of:
                      ["efficient","balanced","factory","performance"].
                      (default: balanced)
--dragon-auto-upgrade
                      Automatically upgrade dragons to latest firmware.
                      (default: False)
--pools POOLS         A JSON blob specifying the pool configuration for
                      dragons. (default: [ { "mac_addresses":[], "pools":[ {
                      "id":0, "url":"stratum+tcp://us-
                      east.stratum.slushpool.com:3333",
                      "username":"brndnmtthws", "password":"x" }, { "id":1,
                      "url":"stratum+tcp://pool.ckpool.org:3333",
                      "username":"3GWdXx9dfLPvSe7d8UnxjnDnSAJodTTbrt",
                      "password":"x" } ] } ] )
--statsd-host STATSD_HOST
                      statsd host to enable statsd metrics (default: None)
--statsd-port STATSD_PORT
                      statsd port (default: 8125)
--statsd-prefix STATSD_PREFIX
                      statsd prefix (default: dragons)
--statsd-interval STATSD_INTERVAL
                      Interval in seconds for fetching metrics and
                      forwarding them to statsd from each dragon (default:
                      60)
```

## Usage

The script is meant to be run continuously within the same local network as your
dragons. The script can be installed with Python's pip by running a `pip install
mother-of-dragons`.

An example systemd unit might look like this (assuming the user
`mother-of-dragons` exists):

```
[Unit]
Description=mother-of-dragons
After=network.target

[Service]
ExecStart=/usr/local/bin/mother-of-dragons \
  --network=10.1.0.0/22 \
  --statsd-host=127.0.0.1 \
  --statsd-port=9125 \
  --dragon-autotune-mode=balanced \
  --dragon-health-reboot \
  --statsd-interval=60 \
  --firmwares-path=/tmp/mod/firmwares \
  --pools='[{"mac_addresses":[],"pools":[{"id":0,"url":"stratum+tcp://us-east.stratum.slushpool.com:3333","username":"brndnmtthws","password":"x"},{"id":1,"url":"stratum+tcp://pool.ckpool.org:3333","username":"3GWdXx9dfLPvSe7d8UnxjnDnSAJodTTbrt","password":"x"}]},{"mac_addresses":["a0:b0:45:00:e3:ab"],"pools":[{"id":0,"url":"stratum+tcp://us-east.stratum.slushpool.com:3333","username":"brndnmtthws","password":"lol"},{"id":1,"url":"stratum+tcp://pool.ckpool.org:3333","username":"3GWdXx9dfLPvSe7d8UnxjnDnSAJodTTbrt","password":"lol"}]}]'
Restart=always
User=mother-of-dragons
Group=users

[Install]
WantedBy=multi-user.target
```

In the example above, the dragon with the MAC address `a0:b0:45:00:e3:ab` will
use a different pool setting than all other dragons.
