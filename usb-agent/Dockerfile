FROM debian:stable
ARG DEBIAN_FRONTEND=noninteractive
RUN apt update && apt -y upgrade

# Install basic build packages
RUN apt -y install curl tar build-essential cmake pkg-config libusb-1.0-0-dev

# Install Python 3.9
RUN apt -y install python3.9-venv

# Prepare for building dependencies
RUN mkdir -p /deps

## TSHARK
# Install from repo
RUN apt install -y tshark

## Build WHSNIFF
WORKDIR /deps
RUN apt -y install jq # jq used in pipe
RUN curl -L https://github.com/homewsn/whsniff/archive/v1.3.tar.gz | tar zx
WORKDIR /deps/whsniff-1.3
RUN make && make install

## Build RTL_433
WORKDIR /deps
RUN apt -y install libtool librtlsdr-dev rtl-sdr
RUN curl -L https://github.com/merbanan/rtl_433/archive/22.11.tar.gz | tar zx
WORKDIR /deps/rtl_433-22.11
RUN cmake .
RUN make && make install

# Install USB-Agent python app
WORKDIR /app
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD [ "python", "-m", "packetzapper-usb-agent"]
