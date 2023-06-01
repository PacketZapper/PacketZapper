from requests import Session
from urllib.parse import urljoin

class PacketZapperSession(Session):
    def __init__(self, base_url=None):
        super().__init__()
        self.base_url = base_url

    def request(self, method, url, *args, **kwargs):
        joined_url = urljoin(self.base_url, url)
        return super().request(method, joined_url, *args, **kwargs)

class PacketZapperClient():
    def __init__(self, hosts: list):
        self.hosts = [PacketZapperSession(base_url) for base_url in hosts]

    def __hosts_generator(self, host_index):
        for i in range(len(self.hosts)):
            if host_index and not i == host_index:
                continue
            yield self.hosts[i]

    def ping_hosts(self, hosts_index=None)-> bool:
        status = False
        for host in self.__hosts_generator(hosts_index):
            host.get("/status").raise_for_status()
            status = True
        return status

    def start_whsniff(self, host_index=None):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.post('/whsniff/start', json={}).json())
        return results

    def stop_whsniff(self, host_index=None):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.post('/whsniff/stop', json={}).json())
        return results


    def start_rtl_433(self, host_index=None, channel=25):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.post('/rtl_433/start', json={'channel': channel}).json())
        return results

    def stop_rtl_433(self, host_index=None):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.post('/rtl_433/stop', json={}).json())
        return results

    def post(self, path, host_index=None, **kwargs):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.post(path, **kwargs))
        return results

    def get(self, path, host_index=None, **kwargs):
        results = []
        for host in self.__hosts_generator(host_index):
            results.append(host.get(path, **kwargs))
        return results