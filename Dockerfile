FROM python:3.7-alpine

RUN cd /tmp \
    && export arch=$(uname -m | sed 's/.*7.*/armhf/') \
    && wget https://bintray.com/ookla/download/download_file?file_path=ookla-speedtest-1.0.0-${ARCH}-linux.tgz -O speedtest.tar.gz \
    && tar xvf speedtest.tar.gz \
    && mv speedtest /usr/bin/ \
    && rm -rf speedtest*

COPY requirements.txt /
RUN pip install --no-cache-dir -r requirements.txt

RUN apk add --no-cache dumb-init

COPY prometheus_speedtest/ /prometheus_speedtest/

EXPOSE 9516/tcp
ENTRYPOINT [ \
    "python", "-m", "prometheus_speedtest.prometheus_speedtest" \
]
CMD [ "--port=9516" ]
