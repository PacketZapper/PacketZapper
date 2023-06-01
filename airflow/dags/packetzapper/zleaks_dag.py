from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.python import PythonSensor
from datetime import datetime, timedelta
from requests import Session
from elasticsearch import Elasticsearch
import elasticsearch

import time

from packetzapper.zleaks import calulate_zr_count, calulate_total_count, calulate_zed_count, calulate_zc_mac
from packetzapper.packetzapper import PacketZapperClient


pz = PacketZapperClient(['http://192.168.1.100:8000'])
es_python = Elasticsearch(hosts=['http://elastic:changeme@elasticsearch:9200'])

def run_inference_tasks():
    print(f"elasticsearch version {elasticsearch.__version__}" )
    devices = calulate_total_count(es_python)
    ZRs = calulate_zr_count(es_python)
    ZEDs = calulate_zed_count(es_python)
    mac = calulate_zc_mac(es_python)
    print(f"There are {ZRs} Zigbee routers, {ZEDs} end devices and a total of {devices} devices. ZC has mac {mac}")

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "ZRs": ZRs,
        "ZEDs": ZEDs,
        'Total': devices,
        "ZC": mac
    }
    es_python.index(index="zleaks_infer", body=results)


default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023, 3, 22)
}

dag = DAG(
    'packetzapper_whsniff',
    default_args=default_args,
    schedule_interval=None,
    catchup=False
)

packetzapper_online_task = PythonSensor(
    task_id='pz_online',
    python_callable=pz.ping_hosts,
    poke_interval=60,
    timeout=120,
    dag=dag
)


packetzapper_start = PythonOperator(
    task_id='pz_start',
    python_callable=pz.start_whsniff,
    dag=dag,
)

packetzapper_sleep = PythonOperator(
    task_id='pz_sleep',
    python_callable=lambda: time.sleep(60*1),
    dag=dag
)

packetzapper_stop = PythonOperator(
    task_id='ps_stop',
    python_callable=pz.stop_whsniff,
    dag=dag

)
zleaks_infer = PythonOperator(
    task_id='zleaks_infer',
    python_callable=run_inference_tasks,
    dag=dag,
)






packetzapper_online_task >> packetzapper_start >> packetzapper_sleep >> packetzapper_stop >> zleaks_infer