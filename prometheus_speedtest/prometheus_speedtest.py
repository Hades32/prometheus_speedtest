#!/usr/bin/python3.7
"""Instrument speedtest.net speedtests from Prometheus."""

from http import server
from urllib.parse import urlparse
import os

from absl import app
from absl import flags
from absl import logging
from prometheus_client import core
import prometheus_client
import subprocess
import json

from prometheus_speedtest import version

flags.DEFINE_string('address', '0.0.0.0', 'address to listen on')
flags.DEFINE_integer('port', 9516, 'port to listen on')
flags.DEFINE_integer(
    'server', None, 'speedtest server to use - leave empty for auto-selection')
flags.DEFINE_boolean('version', False, 'show version')
FLAGS = flags.FLAGS


class Speedtest():
    def __init__(self, source_address=None, server_id=0):
        self._source_address = source_address
        self._server_id = server_id
        self.download = 1  # bps
        self.upload = 1  # bps
        self.ping = 1  # ms
        self.bytes_received = 2
        self.bytes_sent = 2

    def test(self):
        args = ['speedtest', '--accept-license',
                '--accept-gdpr', '--format', 'json']
        if self._server_id:
            args.append('--server-id')
            args.append(str(self._server_id))
        if self._source_address:
            args.append('--ip')
            args.append(str(self._source_address))

        cli_result = subprocess.run(args, stdout=subprocess.PIPE, check=True)
        result = json.loads(cli_result.stdout)
        self.download = result['download']['bandwidth']*8  # bps
        self.bytes_received = result['download']['bytes']
        self.upload = result['upload']['bandwidth']*8  # bps
        self.bytes_sent = result['upload']['bytes']
        self.ping = result['ping']['latency']  # ms
        return self


class PrometheusSpeedtest():
    """Enapsulates behavior performing and reporting results of speedtests."""

    def __init__(self, source_address=None, timeout=10, server_id=None):
        """Instantiates a PrometheusSpeedtest object.

        Args:
            source_address: str - optional network address to bind to.
                e.g. 192.168.1.1.
            timeout: int - optional timeout for speedtest in seconds.
        """
        self._source_address = source_address
        self._timeout = timeout
        self._server_id = server_id

    def test(self):
        """Performs speedtest, returns results.

        Returns:
            speedtest.SpeedtestResults object.
        """
        logging.info('Performing Speedtest')
        client = Speedtest(source_address=self._source_address,
                           server_id=self._server_id)
        results = client.test()
        logging.info(results)
        return results


class SpeedtestCollector():
    """Performs Speedtests when requested from Prometheus."""

    def __init__(self, tester=None, server_id=None):
        """Instantiates a SpeedtestCollector object.

        Args:
            tester: An instantiated PrometheusSpeedtest object for testing.
            server_id: servers-id to use when tester is auto-created
        """
        self._tester = tester if tester else PrometheusSpeedtest(
            server_id=server_id)

    def collect(self):
        """Performs a Speedtests and yields metrics.

        Yields:
            core.Metric objects.
        """
        results = self._tester.test()

        download_speed = core.GaugeMetricFamily('download_speed_bps',
                                                'Download speed (bit/s)')
        download_speed.add_metric(labels=[], value=results.download)
        yield download_speed

        upload_speed = core.GaugeMetricFamily('upload_speed_bps',
                                              'Upload speed (bit/s)')
        upload_speed.add_metric(labels=[], value=results.upload)
        yield upload_speed

        ping = core.GaugeMetricFamily('ping_ms', 'Latency (ms)')
        ping.add_metric(labels=[], value=results.ping)
        yield ping

        bytes_received = core.GaugeMetricFamily('bytes_received',
                                                'Bytes received during test')
        bytes_received.add_metric(labels=[], value=results.bytes_received)
        yield bytes_received

        bytes_sent = core.GaugeMetricFamily('bytes_sent',
                                            'Bytes sent during test')
        bytes_sent.add_metric(labels=[], value=results.bytes_sent)
        yield bytes_sent


class SpeedtestMetricsHandler(server.SimpleHTTPRequestHandler,
                              prometheus_client.MetricsHandler):
    """HTTP handler extending MetricsHandler and adding status page support."""

    def __init__(self, *args, **kwargs):
        static_directory = os.path.join(os.path.dirname(__file__), 'static')
        super(SpeedtestMetricsHandler,
              self).__init__(directory=static_directory, *args, **kwargs)

    def do_GET(self):
        """Handles HTTP GET requests.

        Requests to '/probe' are handled by prometheus_client.MetricsHandler,
        other requests serve static HTML.
        """
        path = urlparse(self.path).path
        if path == '/probe':
            prometheus_client.MetricsHandler.do_GET(self)
        else:
            server.SimpleHTTPRequestHandler.do_GET(self)


def main(argv):
    """Entry point for prometheus_speedtest.py."""
    del argv  # unused
    if FLAGS.version:
        print('prometheus_speedtest v%s' % version.VERSION)
        return

    registry = core.CollectorRegistry(auto_describe=False)
    registry.register(SpeedtestCollector(server_id=FLAGS.server))
    metrics_handler = SpeedtestMetricsHandler.factory(registry)

    http = server.ThreadingHTTPServer((FLAGS.address, FLAGS.port),
                                      metrics_handler)

    logging.info('Starting HTTP server listening on %s:%s', FLAGS.address,
                 FLAGS.port)
    http.serve_forever()


def init():
    """Initializes the prometheus_speedtest cli."""
    app.run(main)


if __name__ == '__main__':
    init()
