[![Build Status](https://travis-ci.org/brndnmtthws/mother-of-dragons.svg?branch=master)](https://travis-ci.org/brndnmtthws/mother-of-dragons) [![Maintainability](https://api.codeclimate.com/v1/badges/b555c676a4940731d47f/maintainability)](https://codeclimate.com/github/brndnmtthws/mother-of-dragons/maintainability) [![Test Coverage](https://api.codeclimate.com/v1/badges/b555c676a4940731d47f/test_coverage)](https://codeclimate.com/github/brndnmtthws/mother-of-dragons/test_coverage) [![PyPI version](https://badge.fury.io/py/mother-of-dragons.svg)](https://badge.fury.io/py/mother-of-dragons)

# 🐲👸🔥🐉 Mother of Dragons 🐲👸🔥🐉

_Be smart. Be mother. Be Mother of Dragons._

DragonMint/Innosilicon T1/T2/B29/B52/A9 management tool based on
[dragon-rest](https://github.com/brndnmtthws/dragon-rest)

![Mom with dragons](/mom.gif?raw=true)

## Features

**Mother of Dragons** can:

- Auto-detect new dragons on your local network and configure them
- Scale easily to 1000s of miners using the [gevent](http://www.gevent.org/)
  library
- Collect metrics from dragons and forward them to statsd
- Automatically update to the latest firmware version when new miners are
  added
- Keep your dragons happy and healthy by rebooting them when they’re sick
- Apply different pool configurations to different dragons based on their
  MAC address
- Should work with both most DragonMint or Innosilicon branded miners
- Free you up from having to manually manage your dragons so you can go
  vacation like a movie star 😎

## How it works

When you run mother-of-dragons, it will start 3 separate closed loops:

- **Scan loop**: scans the local network at a specified interval
  (`main.scan_interval`) looking for dragons. It checks for the dragons by
  making an HTTP request and checking the result. The scan only works if
  your local network allows traffic on port 80 to all the specified IPs,
  which you define with the `main.local_network.network` parameter.

  - When a new dragon is found, the dragon will be configured with the
    desired pool and autotune. If you specify a pool configuration with a MAC
    address, mother will assign the pool config with the matching address.

  - If `auto_upgrade` is set, dragons will be updated to the latest
    firmware version when added.

- **Metrics loop**: fetches metrics from every known dragon according to
  `main.statsd.interval` and forwards those metrics to statsd provided you
  have configured `main.statsd.host`.

- **Health loop**: checks each dragon according to the specified interval
  `health_check_interval` and may (optionally) reboot a dragon if:

  - The dragon has 1 or more devices (ASIC boards) marked as 'Dead'.

  - The dragon has 1 or more devices which have been below
    `health_hashrate_minimum` for at least
    `health_hashrate_duration`.

## Super Quickstart

```
$ pip install mother-of-dragons
$ mother-of-dragons --print-config-toml > config.toml
### Edit config.toml to your liking ###
$ mother-of-dragons --config=config.toml
```

## Configuration

See the [default config.toml](mother_of_dragons/config.toml) for details on
configuration.

## Usage

```
usage: mother-of-dragons [-h] [-c CONFIG] [--print-config-toml]
                         [--print-config-json]

Management tool for DragonMint/Innosilicon miners.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Path to config file in either TOML or JSON format.
                        (default: config.toml)
  --print-config-toml   Print default config in TOML and exit (default: False)
  --print-config-json   Print default config in JSON and exit (default: False)
```

The script is meant to be run continuously within the same local network as
your dragons. The script can be installed with Python's pip by running a
`pip install mother-of-dragons`.

An example systemd unit might look like this (assuming the user
`mother-of-dragons` exists):

```
[Unit]
Description=mother-of-dragons
After=network.target

[Service]
ExecStart=/usr/local/bin/mother-of-dragons \
  --config=config.toml
Restart=always
User=mother-of-dragons
Group=users

[Install]
WantedBy=multi-user.target
```

## Tip Jar

You won't, but just in case:

- BTC: 3EEAE1oKEMnmHGU5Qxibv9mBQyNnes8j8N
- LTC: 3MxmLzTf4sPsFBGYUnX9MMMbTMeaUSox46
