import logging
import argparse
from elasticsearch import Elasticsearch
import uvicorn
import time
import os
import pyfiglet
import json
from . import app, __version__

logging.basicConfig()


logger = logging.getLogger(__package__)

def main():
    banner = pyfiglet.figlet_format('Collection Agent', font='slant')
    parser = argparse.ArgumentParser(prog=__package__, description=f"Welcome to the PacketZapper Collection-Agent!\nThe agent is a simple FastAPI server for managing the execution of sniffing processes.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-v', '--verbose', action='store_true', help='Run with verbose logging')
    parser.add_argument('--es-host', metavar="URL", default=os.getenv('ES_HOST', default='http://127.0.0.1:9200'), help='Elasticsearch host uri')
    parser.add_argument('--es-user', metavar="username", default=os.getenv('ES_USER', default='elastic'), help='Elasticsearch credentials username')
    parser.add_argument('--es-pass', metavar="password", default=os.getenv('ES_PASS', default='changeme'), help='Elasticsearch credentials password')
    parser.add_argument('--es-index', metavar="index", default=os.getenv('ES_INDEX', default='packetzapper'), help="Elasticsearch index for packets (default 'packetzapper')")
    parser.add_argument('--listen-host', metavar="IP", default=os.getenv('LISTEN_HOST', default="0.0.0.0"), help='Web server listen port (default 0.0.0.0)')
    parser.add_argument('--listen-port', metavar="port", default=os.getenv('LISTEN_PORT', default="8000"), help='Web server listen port (default 8000)')

    args = parser.parse_args()
    print(f"{banner}{__package__} version: {__version__}")
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    logger.debug(args)
    app.es = Elasticsearch(hosts=(args.es_host), basic_auth=(args.es_user, args.es_pass))
    while not app.es.ping():
        logger.error("Connection to elasticsearch server failed, check runtime arguments")
        time.sleep(10)
    with open(os.path.join(os.path.dirname(__file__), 'index-template.json'), 'r') as f:
        template_data = json.load(f)
    app.es.indices.put_index_template(name='packetzapper', body=template_data, create=False)
    uvicorn.run(app, host=args.listen_host, port=int(args.listen_port))

if __name__ == "__main__":
    main()