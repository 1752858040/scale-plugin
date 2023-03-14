from kubernetes import client, config
import random
import time
import requests, json

previous_request_num = 0

class Kubernetes:
    def __init__(self):
        config.load_kube_config()
        self.core_api_v1 = client.CoreV1Api()
        self.apps_api_v1 = client.AppsV1Api()

    def scale_deployment_replicas(self, deployment_name, ns_name="default", replicas=1):
        before_resp = self.apps_api_v1.read_namespaced_deployment(name = deployment_name, namespace = ns_name)
        before_resp.spec.replicas = replicas
        ret = self.apps_api_v1.replace_namespaced_deployment(name = deployment_name, namespace=ns_name, body=before_resp)
        if ret:
            return 0
        return 1

    def list_services(self):
        result = []
        ret = self.core_api_v1.list_service_for_all_namespaces(watch=False)
        for i in ret.items:
            info = {'kind': i.kind, 'namespace': i.metadata.namespace, 'name':i.metadata.name,'ip':i.spec.cluster_ip, 'port':i.spec.ports[0].target_port}
            result.append(info)
        return result

    def get_prometheus_address_and_port(self):
        svc = self.list_services()
        for i in svc:
            if i['port'] == 9090:
                return i['ip'] + ':' + str(i['port'])
        return "127.0.0.1:9090"

    def get_container_num(self):
        return 0

# curl 'http://10.97.245.186:9090/api/v1/query_range?
# query=coredns_dns_requests_total&start=1678693235.361&end=1678700435.361&step=28'
def get_coredns_request_total(cluster):
    ret = []
    # prometheus_api_prefix = cluster.get_prometheus_address_and_port()
    prometheus_api_prefix = "127.0.0.1:61059" # debug
    url = "http://" + prometheus_api_prefix + "/" + "api/v1/query?query=coredns_dns_requests_total"
    print(url)
    res = requests.get(url)
    metrics = json.loads(res.text).get('data').get('result')
    request_num = 0
    for metric in metrics:
        if metric['metric']['job'] == 'kubernetes-pods' and metric['metric']['type'] == 'A':
            request_num = metric['value'][1]
            break
    return request_num

def apply_scale(cluster, _deployment_name, _ns_name="default"):
    global previous_request_num
    current_request_num = float(get_coredns_request_total(cluster))
    inc = current_request_num - previous_request_num
    rate = float(inc) / 30
    print("request rate = ", rate)
    pods = random.randint(1, 10)
    ret = cluster.scale_deployment_replicas(deployment_name = _deployment_name, ns_name = _ns_name, replicas=pods)
    if ret == 1:
        return 1
    print(_deployment_name, " scale to ", pods)
    previous_request_num = current_request_num
    return 0

def main():
    print("Init")
    cluster = Kubernetes()
    print("Cluster connected successfully!")
    print(cluster.list_services())
    while apply_scale(cluster, _deployment_name="php-apache") == 0:
        time.sleep(30)

if __name__ == "__main__":
    main()