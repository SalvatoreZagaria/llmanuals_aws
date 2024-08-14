FROM --platform=linux/arm64 python:3.12.5-slim

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y tor privoxy && apt-get clean

RUN sed -i 's/#ControlPort 9051/ControlPort 9051/' /etc/tor/torrc
RUN sed -i 's/#CookieAuthentication 1/CookieAuthentication 0/' /etc/tor/torrc
RUN echo "forward-socks5 / 127.0.0.1:9050 ." >> /etc/privoxy/config

RUN mkdir "/.pip" && \
    echo '[global]\ntrusted-host = pypi.org\n               pypi.python.org\n               files.pythonhosted.org' > /.pip/pip.conf
ENV PIP_CONFIG_FILE=/.pip/pip.conf

COPY requirements.txt /app/requirements.txt
RUN python -m venv /.venv && source /.venv/bin/activate && \
    pip install --no-cache-dir -r /app/requirements.txt && deactivate

ADD app /app
WORKDIR /app
ENV PYTHONPATH=/app

ENTRYPOINT ["./scrape.sh"]
