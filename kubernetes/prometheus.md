# Prometheus

## Setup
Get the project
```
$ git clone https://github.com/prometheus-operator/kube-prometheus.git
```
### Deploy
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
