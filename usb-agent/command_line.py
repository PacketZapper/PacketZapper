import os
import json
from elasticsearch import Elasticsearch


whsniff_cmd = "whsniff -c 25 | tshark -l -T ek -i - | jq --unbuffered -c 'del(.index)'"
rtl433_cmd = "rtl_433 -Fjson -M time:iso:usec:utc -Mlevel"

es_index = "packetzapper"
es_header = {"index":{"_index":es_index}}
es_host = "http://127.0.0.1:9200"
es_user = 'elastic'
es_pass = 'changeme'

es = Elasticsearch(hosts=(es_host), basic_auth=(es_user, es_pass))

stream = os.popen(rtl433_cmd, 'r', 1)
es_data = []
for line in stream:
    data = json.loads(line)
    es_data.append(es_header)
    es_data.append(data)
    print(line)
    if len(es_data) == 2:
        es.bulk(index=es_index, operations=es_data)
        print(es.count(index=es_index))
        es_data.clear()
