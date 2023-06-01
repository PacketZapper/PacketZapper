#!/usr/bin/env python
import datetime

from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Response
from fastapi.responses import JSONResponse
from elasticsearch import Elasticsearch
import asyncio
import subprocess, shlex
import json
import os
import io
import time
import signal
import logging
import argparse
from enum import Enum
from pydantic import BaseModel, Field
from typing import Union, Generator, Callable

logger = logging.getLogger(__name__)

processes = {}
ES_INDEX = "packetzapper"
ES_HEADER = {"index": {"_index": ES_INDEX}}

app = FastAPI()
app.es: Elasticsearch = None # is initialized elsewhere (eg __main__)

class ErrorResponse(BaseModel):
    message: str

class ProcessesStatus(BaseModel):
    pid: int
    exit_code: Union[int, None]
    cmd: str
    running: bool

class StatusResponse(BaseModel):
    processes: list[ProcessesStatus] = Field(example=ProcessesStatus(pid=1234, exit_code=-17, cmd='ls -lha', running=False))

class SniffRequest(BaseModel):
    batch_size: int = Field(default=5, description="How many lines to send per batch job to elasticsearch")
    sniffer: str = "base"

class WhsniffRequest(SniffRequest):
    sniffer: str = "whsniff"
    channel: int = Field(default=25, description="Whsniff Zigbee channel", ge=1, le=26)
    display_filter: str = Field(default="", description="Tshark display filter")



class RTL_433Request(SniffRequest):
    sniffer = "rtl_433"
    batch_size = 1
    device: str = "0"
    extra_args: str = "-Mlevel"


class StartResponse(BaseModel):
    started: bool
    request: Union[WhsniffRequest, RTL_433Request]
    pid: Union[int,None]
    message: str = "Started service"

class StopRequest(BaseModel):
    pid: int = 0

class StopResponse(BaseModel):
    stopped: bool
    message: str = "Stopped service"
    results: list = []

responses = {
    503: {"model": ErrorResponse},
}

def cmd_replacement(cmd: str, model):
    for key, key_upper in [(str(key), str(key).upper()) for key in model.dict()]:
        if key_upper in cmd:
            cmd = cmd.replace(key_upper, str(model.dict()[key]))
    return cmd

def run_cmd(cmd) -> subprocess.Popen:
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=os.setsid)
    return process


def stop_pid(pid_request: int, group: dict) -> list:
    stop_results = []
    for process, pid in [(group[pid], pid) for pid in group]:
        if pid_request == 0 or pid_request == pid:
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            stop_results.append({"pid": pid, "exitcode": process.poll()})
            if process.poll is not None:
                del(processes[pid])
    return stop_results


def stream_process_json(process: subprocess.Popen) -> Generator[dict, None, None]:
    while True:
        a = process.poll()
        if process.poll() is not None:
            logger.error(process.stderr.read())
            break
        try:
            yield json.loads(process.stdout.readline())
        except:
            continue


def formatter_whsniff(process: subprocess.Popen) -> Generator[dict, None, None]:
    for data in stream_process_json(process):
        if not 'timestamp' in data.keys():
            continue
        data['timestamp'] = datetime.datetime.utcfromtimestamp(int(data['timestamp']) / 1000).isoformat()
        yield data


def formatter_rtl_433(process: subprocess.Popen) -> Generator[dict, None, None]:
    for data in stream_process_json(process):
        data['timestamp'] = datetime.datetime.utcnow().isoformat()
        yield data


def stream_to_es(process, formatter: staticmethod, request: BaseModel, batch_size=10):
    es_data = []
    for line in formatter(process):
        es_data.append(ES_HEADER)
        es_data.append({**line, 'packetzapper': {'request': request.dict()}})
        if len(es_data) >= batch_size*2:
            r = app.es.bulk(index=ES_INDEX, operations=es_data)
            es_data.clear()
    logger.info(f"Stopped streaming {process}")

def get_processes_status(group: dict):
    return StatusResponse(processes=[ProcessesStatus(pid=a, exit_code=group[a].poll(), cmd=group[a].args, running=group[a].poll() is None) for a in group])

def filter_processes(filter_value):
    return {k: v for (k, v) in processes.items() if str(processes[k].args).startswith(filter_value)}

@app.on_event("startup")
async def on_startup():
    logger.info("Started web server")
    pass


@app.get('/whsniff/status', responses={**responses, 200: {"model": StatusResponse}})
async def whsniff_status():
    return get_processes_status(filter_processes('whsniff'))


@app.get('/rtl_433/status', responses={**responses, 200: {"model": StatusResponse}})
async def rtl_433_status():
    return get_processes_status(filter_processes('rtl_433'))


@app.post('/whsniff/start', responses={**responses, 200: {"model": StartResponse}})
async def whsniff_start(background_tasks: BackgroundTasks, sniff_request: WhsniffRequest):
    WHSNIFF_CMD = "whsniff -c CHANNEL | tshark -l -T ek -i - -Y 'DISPLAY_FILTER' | jq --unbuffered -c 'del(.index)'"
    process = run_cmd(cmd_replacement(WHSNIFF_CMD, sniff_request))
    await asyncio.sleep(1)
    if process.poll() is not None:
        return JSONResponse(status_code=503, content={'message': str(process.stderr.read())})
    processes[process.pid] = process
    background_tasks.add_task(stream_to_es, process, formatter_whsniff, sniff_request, 100)
    return StartResponse(request=sniff_request, started=True, pid=process.pid)


@app.post('/rtl_433/start', responses={**responses, 200: {"model": StartResponse}})
async def rtl_433_start(background_tasks: BackgroundTasks, sniff_request: RTL_433Request):
    RTL_433_CMD = "rtl_433 -d DEVICE -Fjson -M time:iso:usec:utc EXTRA_ARGS | cat"
    process = run_cmd(cmd_replacement(RTL_433_CMD, sniff_request))
    await asyncio.sleep(1)
    if process.poll() is not None:
        return StartResponse(request=sniff_request, started=False, pid=process.pid, message=process.stderr.read())
    processes[process.pid] = process
    background_tasks.add_task(stream_to_es, process, formatter_rtl_433, sniff_request, 1)
    return StartResponse(request=sniff_request, started=True, pid=process.pid)


@app.post('/whsniff/stop', responses={**responses, 200: {"model": StopResponse}})
async def whsniff_stop(stop_request: StopRequest):
    result = stop_pid(stop_request.pid, filter_processes('whsniff'))
    return StopResponse(stopped=len(result)>0, results=result)


@app.post('/rtl_433/stop', responses={**responses, 200: {"model": StopResponse}})
async def rtl_433_stop(stop_request: StopRequest):
    result = stop_pid(stop_request.pid, filter_processes('rtl_433'))
    return StopResponse(stopped=len(result)>0, results=result)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/status")
async def status():
    return {"status": "online"}






