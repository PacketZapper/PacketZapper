# PacketZapper

PacketZapper is an Automated Collection and Processing Platform for IoT Device Traffic. This Git repository contains the platform code, including an example inference DAG.

## Installation

PacketZapper requires Docker and docker-compose to be installed on the host. We reccomend using a linux based operating system such as Ubuntu 20.04. 

First clone the repository to a directory containing a sufficient amount of disk space. We use bind mounts to persist all collected data.
```bash
git clone https://github.com/PacketZapper/PacketZapper.git
cd PacketZapper
```

Modify the `.env` files in the `./airflow`, `./elasticsearch`, `./jupyter` and `./usb-agent` directories, such as changing the default password from `changeme`.

Start all the services:

```bash
docker compose -f ./airflow/docker-compose.yml -f -f ./elasticsearch/docker-compose.yml -f ./jupyter/docker-compose.yml -f ./usb-agent/docker-compose.yml up -d
```

## Usage

Here is an overview over the different web bindings:

| Service | URL | Description |
|---|---|--|
| Collection Agent | http://127.0.0.1:8000/ | API for controlling collection. See the /docs path for more details |
| Elasticsearch | http://127.0.0.1:9200/ | Elasticsearch API endpoint. Does not have a UI |
| Kibana | http://127.0.0.1:5601/ | Easiest way to interact with the elasticsearch data |
| Apache Airflow | http://127.0.0.1:8080/ | Control and view DAGs on the system |
| JupyterLab | http://127.0.0.1:8888/ | General workspace |