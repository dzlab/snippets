### Setup prometeus
Note the following works with Helm v3 (Tillerless)
- https://medium.com/@savvythrough/helm-v3-a-tillerless-strategy-1bbc724e3480

Install Helm's client side component https://helm.sh/docs/intro/
```
$ brew install helm
```

Search for prometeus charts
```
➜  ~ helm search hub prometheus-operator
URL                                               	CHART VERSION	APP VERSION	DESCRIPTION                                       
https://hub.helm.sh/charts/choerodon/prometheus...	8.5.8        	8.5.8      	Provides easy monitoring definitions for Kubern...
https://hub.helm.sh/charts/cloudposse/prometheu...	0.2.0        	           	Provides easy monitoring definitions for Kubern...
https://hub.helm.sh/charts/cloudposse/prometheus  	0.2.1        	           	Prometheus instance created by the CoreOS Prome...
https://hub.helm.sh/charts/stable/prometheus-op...	8.13.0       	0.38.1     	Provides easy monitoring definitions for Kubern...
https://hub.helm.sh/charts/bitnami/prometheus-o...	0.15.2       	0.38.1     	The Prometheus Operator for Kubernetes provides...
```

In Helm 3, the stable repository is not set and has to be added manually:
```
$ helm repo add --help
add a chart repository

Usage:
  helm repo add [NAME] [URL] [flags]
$ helm repo add stable https://kubernetes-charts.storage.googleapis.com
```

Update the Helm repository and fetch up-to-date charts locally from public repositories.
```
$ helm repo update
```
Create a monitoring namespace using `kubectl create` command
```
$ kubectl create namespace monitoring
```

Deploy Prometheus Operator in the monitoring namespace using `helm install`. This command will deploy a bundle of components needed to use Prometheus on Kuernetes, which are Prometheus, Alertmanager, Grafana, the node-exporter and kube-state-metrics addon.
```
$ helm install prometheus stable/prometheus-operator --namespace monitoring
NAME: prometheus
LAST DEPLOYED: Tue Apr 21 10:55:07 2020
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
NOTES:
The Prometheus Operator has been installed. Check its status by running:
  kubectl --namespace monitoring get pods -l "release=prometheus"

Visit https://github.com/coreos/prometheus-operator for instructions on how
to create & configure Alertmanager and Prometheus instances using the Operator.
```

Get the list of services in the monitoring namespace:
```
$ kubectl get svc -n monitoring
```

Verify the status of the pods deployed in the monitoring namespace:
```
$ kubectl get pods -n monitoring
NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-prometheus-prometheus-oper-alertmanager-0   2/2     Running   0          5m30s
prometheus-grafana-865db569c6-bx46t                      2/2     Running   0          5m42s
prometheus-kube-state-metrics-6d6fc7946-qmlns            1/1     Running   0          5m43s
prometheus-prometheus-node-exporter-nzgz7                1/1     Running   0          5m43s
prometheus-prometheus-oper-operator-9f9b56b48-pjkfp      2/2     Running   0          5m43s
prometheus-prometheus-prometheus-oper-prometheus-0       3/3     Running   1          5m19s
```

#### prometeus UI
Find the Prometeus service running on the monitoring namespace
```
$ kubectl get svc -n monitoring         
NAME                                      TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
alertmanager-operated                     ClusterIP   None             <none>        9093/TCP,9094/TCP,9094/UDP   15m
metrics-server                            ClusterIP   10.106.232.100   <none>        443/TCP                      15m
prometheus-grafana                        ClusterIP   10.110.93.64     <none>        80/TCP                       15m
prometheus-kube-state-metrics             ClusterIP   10.105.244.24    <none>        8080/TCP                     15m
prometheus-operated                       ClusterIP   None             <none>        9090/TCP                     15m
prometheus-prometheus-node-exporter       ClusterIP   10.111.11.19     <none>        9100/TCP                     15m
prometheus-prometheus-oper-alertmanager   ClusterIP   10.98.140.68     <none>        9093/TCP                     15m
prometheus-prometheus-oper-operator       ClusterIP   10.102.56.60     <none>        8080/TCP,443/TCP             15m
prometheus-prometheus-oper-prometheus     ClusterIP   10.98.211.172    <none>        9090/TCP                     15m
```

Create a port forwarding to access the Prometheus UI using `kubectl port-forward` to forward the local port 9090 to Grafana UI port 9090 in running Prometheus service:
```
$ kubectl port-forward -n monitoring svc/prometheus-prometheus-oper-prometheus 9090:9090
```
Now you can visit Prometheus UI on http://localhost:8000/targets.


#### Grafana UI

Create a port forwarding to access the Grafana UI using `kubectl port-forward` to forward the local port 8000 to Grafana UI port 3000 in running Grafana pod:
```
$ kubectl port-forward -n monitoring prometheus-grafana-865db569c6-bx46t 8000:3000
```
Now you can visit Grafana UI on http://localhost:8000/ and login with username `admin` and password `prom-operator`.

Similarly, we can access Grafana UI after establishing a proxy connection to kubernetes as follows:
```
$ kubectl proxy --port=8080
```
Now we can visit Grafana UI on http://localhost:8001/api/v1/namespaces/monitoring/services/http:prometheus-grafana:service/proxy/login# (check if monitoring namespace is correct)
The pattern of the URL is like this http://localhost:8080/api/v1/proxy/namespaces/<NAMESPACE>/services/<SERVICE-NAME>:<PORT-NAME>/

Resources
- github.com/k8sdevopscookbook/src
- Helm v2 https://medium.com/faun/trying-prometheus-operator-with-helm-minikube-b617a2dccfa3
- https://github.com/bakins/minikube-prometheus-demo
- https://sysdig.com/blog/kubernetes-monitoring-prometheus/
- https://linuxacademy.com/hands-on-lab/f50277f4-3140-44d7-aeb9-b56400c7670f/
- https://itnext.io/kubernetes-monitoring-with-prometheus-in-15-minutes-8e54d1de2e13
- https://www.replex.io/blog/kubernetes-in-production-the-ultimate-guide-to-monitoring-resource-metrics-with-grafana

### Setup Grafana
Using community dashoard https://grafana.com/grafana/dashboards/6417 we can configure it as follows

* Copy dashboard ID `6417`
* On Grafana UI, the left panel click `+` then choose `import` option
* Type in the ID `6417` and click load

In the next page, choose Prometheus data source and confirm

### Alerting with Grafana
The following steps illustrate an example of setting up an alert.
* On Grafana dashboard, create a panel this will take you to panel dashboard
* On query tab, set one like `kube_node_status_allocatable_pods{node=~".*"}`
* On alert tab, set up a condition on the query, e.g. avg > 100
* You can test the rule by clicking on `Test Rule` button to the right.

Back to the Grafana dashboard, the Alerting tab displays the alert rule, you can specify notifications channel so that alerts are routed to it.

The following resource explains how to setup a slack notifications channel, and setup Grafana alerting to push slack notifications:
https://medium.com/@_oleksii_/grafana-alerting-and-slack-notifications-3affe9d5f688
  
https://medium.com/zolo-engineering/configuring-prometheus-operator-helm-chart-with-aws-eks-c12fac3b671a
