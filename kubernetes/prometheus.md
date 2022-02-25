# Prometheus

## With HELM
### On EKS
- https://aws-quickstart.github.io/quickstart-eks-prometheus/
- https://www.eksworkshop.com/intermediate/240_monitoring/deploy-prometheus/


### Option 1
See https://kruschecompany.com/kubernetes-prometheus-operator/

Install prometheus-operator helm chart
```
$ helm install prometheus stable/prometheus-operator --namespace monitoring
```
Check prometheus services are started
```
$ kubectl get pod -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-prometheus-prometheus-oper-alertmanager-0   2/2     Running   0          42s
prometheus-grafana-78444cbd5c-zw6mp                      2/2     Running   0          48s
prometheus-kube-state-metrics-5f89586745-jgxjk           1/1     Running   0          48s
prometheus-prometheus-node-exporter-5lw88                1/1     Running   0          48s
prometheus-prometheus-node-exporter-5sv4t                1/1     Running   0          48s
prometheus-prometheus-node-exporter-8t9fs                1/1     Running   0          48s
prometheus-prometheus-node-exporter-gfljz                1/1     Running   0          48s
prometheus-prometheus-node-exporter-z4g6g                1/1     Running   0          48s
prometheus-prometheus-oper-operator-6d9c4bdb9f-4v77q     2/2     Running   0          48s
prometheus-prometheus-prometheus-oper-prometheus-0       3/3     Running   1          32s
```

Expose grafana externally with Load Balancer
```
$ kubectl expose deployment prometheus-grafana --port=3000 --target-port=3000 --name=grafana-service --type=LoadBalancer --namespace monitoring
```

You can check it was exposed properly by locating the service
```
$ k get svc -n monitoring 
NAME                                      TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
grafana-service                           LoadBalancer   10.31.231.71    xx.xx.xx.xx   3000:30401/TCP               2m10s
```

Now deployServiceMonitors. Prometheus discovers ServiceMonitors by label. You need to know which ServiceMonitors label it is looking for (here `release: prometheus`). To do this:

kubectl get prometheuses.monitoring.coreos.com -oyaml
We are looking for the serviceMonitorSelector block:
```
$ kubectl get prometheuses.monitoring.coreos.com -o yaml -n monitoring
...
    serviceMonitorNamespaceSelector: {}
    serviceMonitorSelector:
      matchLabels:
        release: prometheus
...
```

Create a service monitor object for your serivce `myapp-metrics-service.yaml ` (notice how we are using `release: prometheus` label), also this assumes our app has a port named `metrics` and that metrics can be grabed from path `/metrics`.
```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: myapp
  labels:
    release: prometheus
    app: myapp-metrics
spec:
  endpoints:
  - port: metrics
    path: '/metrics'
  namespaceSelector:
    matchNames:
      - mynamespace
  selector:
    matchLabels:
      myappLabel: myappLabelValue
```
Create the service monitor object
```
$ kubectl apply -f myapp-metrics-service.yaml -n monitoring  
```
Check that our service monitor was created
```
$ kubectl get servicemonitors.monitoring.coreos.com -n monitoring
NAME                                                 AGE
myapp                                                70s
prometheus-prometheus-oper-alertmanager              41m
prometheus-prometheus-oper-apiserver                 41m
prometheus-prometheus-oper-coredns                   41m
prometheus-prometheus-oper-grafana                   41m
prometheus-prometheus-oper-kube-controller-manager   41m
prometheus-prometheus-oper-kube-etcd                 41m
prometheus-prometheus-oper-kube-proxy                41m
prometheus-prometheus-oper-kube-scheduler            41m
prometheus-prometheus-oper-kube-state-metrics        41m
prometheus-prometheus-oper-kubelet                   41m
prometheus-prometheus-oper-node-exporter             41m
prometheus-prometheus-oper-operator                  41m
prometheus-prometheus-oper-prometheus                41m
```

Open connection to prometheus
```
$ kubectl port-forward prometheus-prometheus-prometheus-oper-prometheus-0 9090:9090 -n monitoring
```

### Option 2
```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
NAME: prometheus
LAST DEPLOYED: Thu Oct 21 14:34:31 2021
NAMESPACE: monit
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
The Prometheus server can be accessed via port 80 on the following DNS name from within your cluster:
prometheus-server.monit.svc.cluster.local


Get the Prometheus server URL by running these commands in the same shell:
  export POD_NAME=$(kubectl get pods --namespace monit -l "app=prometheus,component=server" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace monit port-forward $POD_NAME 9090


The Prometheus alertmanager can be accessed via port 80 on the following DNS name from within your cluster:
prometheus-alertmanager.monit.svc.cluster.local


Get the Alertmanager URL by running these commands in the same shell:
  export POD_NAME=$(kubectl get pods --namespace monit -l "app=prometheus,component=alertmanager" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace monit port-forward $POD_NAME 9093
#################################################################################
######   WARNING: Pod Security Policy has been moved to a global property.  #####
######            use .Values.podSecurityPolicy.enabled with pod-based      #####
######            annotations                                               #####
######            (e.g. .Values.nodeExporter.podSecurityPolicy.annotations) #####
#################################################################################


The Prometheus PushGateway can be accessed via port 9091 on the following DNS name from within your cluster:
prometheus-pushgateway.monit.svc.cluster.local


Get the PushGateway URL by running these commands in the same shell:
  export POD_NAME=$(kubectl get pods --namespace monit -l "app=prometheus,component=pushgateway" -o jsonpath="{.items[0].metadata.name}")
  kubectl --namespace monit port-forward $POD_NAME 9091

For more information on running Prometheus, visit:
https://prometheus.io/
```
Prometheus pods created in the cluster.
```
$ k get pods -n monit
NAME                                             READY   STATUS    RESTARTS   AGE
prometheus-alertmanager-56d55d776-mpcds          2/2     Running   0          98s
prometheus-kube-state-metrics-58c5cd6ddb-fg8hc   1/1     Running   0          98s
prometheus-node-exporter-9g28n                   1/1     Running   0          98s
prometheus-node-exporter-mfqk9                   1/1     Running   0          98s
prometheus-node-exporter-qd48r                   1/1     Running   0          98s
prometheus-node-exporter-qggt5                   1/1     Running   0          98s
prometheus-node-exporter-wq9hk                   1/1     Running   0          98s
prometheus-pushgateway-68b8b68999-ffxm9          1/1     Running   0          98s
prometheus-server-74ccdfcc-gljxm                 2/2     Running   0          98s
```

```
$ kubectl get cm prometheus-server -o yaml -n monit
```
<details><summary>Example output</summary>
<p>

```
apiVersion: v1
data:
  alerting_rules.yml: |
    {}
  alerts: |
    {}
  prometheus.yml: |
    global:
      evaluation_interval: 1m
      scrape_interval: 1m
      scrape_timeout: 10s
    rule_files:
    - /etc/config/recording_rules.yml
    - /etc/config/alerting_rules.yml
    - /etc/config/rules
    - /etc/config/alerts
    scrape_configs:
    - job_name: prometheus
      static_configs:
      - targets:
        - localhost:9090
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-apiservers
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: default;kubernetes;https
        source_labels:
        - __meta_kubernetes_namespace
        - __meta_kubernetes_service_name
        - __meta_kubernetes_endpoint_port_name
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-nodes
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - replacement: kubernetes.default.svc:443
        target_label: __address__
      - regex: (.+)
        replacement: /api/v1/nodes/$1/proxy/metrics
        source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
      job_name: kubernetes-nodes-cadvisor
      kubernetes_sd_configs:
      - role: node
      relabel_configs:
      - action: labelmap
        regex: __meta_kubernetes_node_label_(.+)
      - replacement: kubernetes.default.svc:443
        target_label: __address__
      - regex: (.+)
        replacement: /api/v1/nodes/$1/proxy/metrics/cadvisor
        source_labels:
        - __meta_kubernetes_node_name
        target_label: __metrics_path__
      scheme: https
      tls_config:
        ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        insecure_skip_verify: true
    - job_name: kubernetes-service-endpoints
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scrape
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_service_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_service_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: kubernetes_namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_service_name
        target_label: kubernetes_name
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_node_name
        target_label: kubernetes_node
    - job_name: kubernetes-service-endpoints-slow
      kubernetes_sd_configs:
      - role: endpoints
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_service_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_service_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: kubernetes_namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_service_name
        target_label: kubernetes_name
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_node_name
        target_label: kubernetes_node
      scrape_interval: 5m
      scrape_timeout: 30s
    - honor_labels: true
      job_name: prometheus-pushgateway
      kubernetes_sd_configs:
      - role: service
      relabel_configs:
      - action: keep
        regex: pushgateway
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_probe
    - job_name: kubernetes-services
      kubernetes_sd_configs:
      - role: service
      metrics_path: /probe
      params:
        module:
        - http_2xx
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_service_annotation_prometheus_io_probe
      - source_labels:
        - __address__
        target_label: __param_target
      - replacement: blackbox
        target_label: __address__
      - source_labels:
        - __param_target
        target_label: instance
      - action: labelmap
        regex: __meta_kubernetes_service_label_(.+)
      - source_labels:
        - __meta_kubernetes_namespace
        target_label: kubernetes_namespace
      - source_labels:
        - __meta_kubernetes_service_name
        target_label: kubernetes_name
    - job_name: kubernetes-pods
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scrape
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: kubernetes_namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_name
        target_label: kubernetes_pod_name
      - action: drop
        regex: Pending|Succeeded|Failed|Completed
        source_labels:
        - __meta_kubernetes_pod_phase
    - job_name: kubernetes-pods-slow
      kubernetes_sd_configs:
      - role: pod
      relabel_configs:
      - action: keep
        regex: true
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scrape_slow
      - action: replace
        regex: (https?)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_scheme
        target_label: __scheme__
      - action: replace
        regex: (.+)
        source_labels:
        - __meta_kubernetes_pod_annotation_prometheus_io_path
        target_label: __metrics_path__
      - action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        source_labels:
        - __address__
        - __meta_kubernetes_pod_annotation_prometheus_io_port
        target_label: __address__
      - action: labelmap
        regex: __meta_kubernetes_pod_annotation_prometheus_io_param_(.+)
        replacement: __param_$1
      - action: labelmap
        regex: __meta_kubernetes_pod_label_(.+)
      - action: replace
        source_labels:
        - __meta_kubernetes_namespace
        target_label: kubernetes_namespace
      - action: replace
        source_labels:
        - __meta_kubernetes_pod_name
        target_label: kubernetes_pod_name
      - action: drop
        regex: Pending|Succeeded|Failed|Completed
        source_labels:
        - __meta_kubernetes_pod_phase
      scrape_interval: 5m
      scrape_timeout: 30s
    alerting:
      alertmanagers:
      - kubernetes_sd_configs:
          - role: pod
        tls_config:
          ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
        relabel_configs:
        - source_labels: [__meta_kubernetes_namespace]
          regex: monit
          action: keep
        - source_labels: [__meta_kubernetes_pod_label_app]
          regex: prometheus
          action: keep
        - source_labels: [__meta_kubernetes_pod_label_component]
          regex: alertmanager
          action: keep
        - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_probe]
          regex: .*
          action: keep
        - source_labels: [__meta_kubernetes_pod_container_port_number]
          regex: "9093"
          action: keep
  recording_rules.yml: |
    {}
  rules: |
    {}
kind: ConfigMap
metadata:
  annotations:
    meta.helm.sh/release-name: prometheus
    meta.helm.sh/release-namespace: monit
  creationTimestamp: "2021-10-21T21:34:40Z"
  labels:
    app: prometheus
    app.kubernetes.io/managed-by: Helm
    chart: prometheus-14.11.0
    component: server
    heritage: Helm
    release: prometheus
  name: prometheus-server
  namespace: monit
  resourceVersion: "44584890"
  uid: de3486b4-af5a-44c3-a874-eed6d2a7b100
```
</p>
</details>

### References
- https://sysdig.com/blog/kubernetes-monitoring-prometheus/

## With kube-prometheus
### Setup
Get the project
```
$ git clone https://github.com/prometheus-operator/kube-prometheus.git
```
#### Deploy
Create the namespace and CRDs
```
$ kubectl create -f manifests/setup
```
Wait for them to be availble
```
$ until kubectl get servicemonitors --all-namespaces ; do date; sleep 1; echo ""; done
```
Create remaining resources
```
$ kubectl create -f manifests/
```

## References
- Prometheus operator quick start- [link](https://prometheus-operator.dev/docs/prologue/quick-start/)
- kube-prometheus a complete monitoring stack using jsonnet - [link](https://elastisys.com/kube-prometheus-a-complete-monitoring-stack-using-jsonnet/)
- Prometheus Operator – Installing Prometheus Monitoring Within The Kubernetes Environment [link](https://kruschecompany.com/kubernetes-prometheus-operator/)
- Prometheus operator API Documentation [link](https://github.com/prometheus-operator/prometheus-operator/blob/master/Documentation/api.md)
