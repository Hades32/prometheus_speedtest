# Prometheus Speedtest

This is a fork from [jeanralphaviles/prometheus_speedtest](https://github.com/jeanralphaviles/prometheus_speedtest.git) but using the official CLI tool with JSON output as the underlying library is not fast enough for Gigabit networks. It's excpected to be used via the Docker Image only.

Instrument [Speedtest.net](http://speedtest.net) tests from
[Prometheus](https://prometheus.io). Provides metrics on download\_speed,
upload\_speed, and latency.

[![Docker Build Status](https://img.shields.io/docker/build/jraviles/prometheus_speedtest.svg)](https://hub.docker.com/r/hades32/prometheus_speedtest/)

![Grafana](https://github.com/jeanralphaviles/prometheus_speedtest/raw/master/images/grafana.png)

## Running with Docker

`prometheus_speedtest` is also available as a [Docker](http://docker.com) image
on [Docker Hub](https://hub.docker.com/r/jraviles/prometheus_speedtest)
:whale:.

```shell
docker run --rm -d --name prometheus_speedtest -p 9516:9516/tcp jraviles/prometheus_speedtest:latest
```

## Integrating with Prometheus

`prometheus_speedtest` is best when paired with
[Prometheus](https://prometheus.io). Prometheus can be configured to perform
Speedtests on an interval and record their results.

Speedtest metrics available to query in Prometheus.

| Metric Name           | Description                 |
|---------------------- |---------------------------- |
| download\_speed\_bps  | Download speed (bit/s)      |
| upload\_speed\_bps    | Upload speed (bit/s)        |
| ping\_ms              | Latency (ms)                |
| bytes\_received       | Bytes received during test  |
| bytes\_sent           | Bytes sent during test      |

### prometheus.yml config

Add this to your
[Prometheus config](https://prometheus.io/docs/prometheus/latest/configuration/configuration)
to start instrumenting Speedtests and recording their metrics.

```yaml
global:
  scrape_timeout: 2m

scrape_configs:
- job_name: 'speedtest'
  metrics_path: /probe
  static_configs:
  - targets:
    - localhost:9516
```

Note if you're running `prometheus` under Docker, you must link the
`prometheus` container to `prometheus_speedtest`. See the steps below for how
this can be done.

### Deploying multi-architecture images to Docker Hub

1. Ensure that Docker >= 19.03 and
   [docker buildx](https://docs.docker.com/buildx/working-with-buildx/) is
   installed.

1. Build and push the new image.

   ```shell
   # Ensure you have run 'docker login'
   export DOCKER_CLI_EXPERIMENTAL=enabled
   docker buildx create --use --name my-builder
   docker buildx build --push --platform linux/amd64,linux/arm64,linux/arm/v7 \
       -t hades32/prometheus_speedtest:latest .
   docker buildx rm my-builder
   ```

## Authors

* Orignal by: Jean-Ralph Aviles
* Fork by: Martin Rauscher

## License

This product is licensed under the Apache 2.0 license. See [LICENSE](LICENSE)
file for details.

## Acknowledgments

* The Prometheus team <https://prometheus.io>
* Testing in Python team <http://lists.idyll.org/listinfo/testing-in-python>
* Benjamin Staffin [python-glog](https://github.com/benley/python-glog)
