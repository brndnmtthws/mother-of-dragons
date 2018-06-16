from pytest import fixture
from mother_of_dragons.statsd_wrapper import StatsdWrapper
from mother_of_dragons.mother import Mother
from statsd import StatsClient


def test_statsd_present(mocker):
    mocker.patch.object(StatsClient, 'incr', autospec=True)
    statsd = StatsdWrapper(
        host='localhost',
        port=1234,
        prefix='herp',
    )
    statsd.incr('counter')
    StatsClient.incr.assert_called_once_with(statsd.statsd, 'counter')

def test_statsd_not_present(mocker):
    mocker.patch.object(StatsClient, 'incr', autospec=True)
    statsd = StatsdWrapper(
        host=None,
        port=1234,
        prefix='herp',
    )
    statsd.incr('counter')
    StatsClient.incr.assert_not_called()
