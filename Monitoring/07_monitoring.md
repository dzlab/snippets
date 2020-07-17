### App monitoring
https://sysdig.com/blog/kubernetes-monitoring-prometheus-operator-part3/

Create a service for a deployment
```
$ kubectl get pods -l 'spark-role=driver' --all-namespaces
NAMESPACE                                           NAME                                  READY   UP-TO-DATE   AVAILABLE   AGE
local-env-k8sns-exmacstandaloneexmachinatestba-01   exmacstandaloneexmachinatestba        1/1     1            1           3d18h
$ kubectl expose deployment/exmacstandaloneexmachinatestba -n local-env-k8sns-exmacstandaloneexmachinatestba-01
Error from server (AlreadyExists): services "exmacstandaloneexmachinatestba" already exists
```
The service exists but it is of type NodePort not a simple service. Thus we create a service with following yaml
```yaml
apiVersion: v1
kind: Service
metadata:
  name: exmacstandaloneexmachinatestba-svc
  labels:
    spark-role: driver
spec:
  ports:
  - port: 9091
    protocol: TCP
  selector:
    spark-role: driver
```

See Prometheus Operator [user guide](https://github.com/coreos/prometheus-operator/blob/master/Documentation/user-guides/getting-started.md) for how to setup the different components. Also see https://managedkube.com/prometheus/operator/servicemonitor/troubleshooting/2019/11/07/prometheus-operator-servicemonitor-troubleshooting.html

1. Check the name of the Prometheus object created in the monitoring namespace
```
$ kubectl get prometheus -n monit
NAME                                    VERSION   REPLICAS   AGE
prometheus-prometheus-oper-prometheus   v2.16.0   1          4h10m
```

Now check the description of this object for the Pod selector and Service Monitor selector.
```
$ kubectl describe prometheus prometheus-prometheus-oper-prometheus -n monit
Name:         prometheus-prometheus-oper-prometheus
Namespace:    monit
Labels:       app=prometheus-operator-prometheus
              chart=prometheus-operator-8.13.0
              heritage=Helm
              release=prometheus
Annotations:  <none>
API Version:  monitoring.coreos.com/v1
Kind:         Prometheus
Metadata:
  Creation Timestamp:  2020-06-05T17:32:52Z
  Generation:          1
  Resource Version:    2509
  Self Link:           /apis/monitoring.coreos.com/v1/namespaces/monit/prometheuses/prometheus-prometheus-oper-prometheus
  UID:                 5e23a07f-a1b9-49be-a3c9-8a05fe51f61b
Spec:
  Alerting:
    Alertmanagers:
      API Version:   v2
      Name:          prometheus-prometheus-oper-alertmanager
      Namespace:     monit
      Path Prefix:   /
      Port:          web
  Base Image:        quay.io/prometheus/prometheus
  Enable Admin API:  false
  External URL:      http://prometheus-prometheus-oper-prometheus.monit:9090
  Listen Local:      false
  Log Format:        logfmt
  Log Level:         info
  Paused:            false
  Pod Monitor Namespace Selector:
  Pod Monitor Selector:
    Match Labels:
      Release:   prometheus
  Port Name:     web
  Replicas:      1
  Retention:     10d
  Route Prefix:  /
  Rule Namespace Selector:
  Rule Selector:
    Match Labels:
      App:      prometheus-operator
      Release:  prometheus
  Security Context:
    Fs Group:            2000
    Run As Non Root:     true
    Run As User:         1000
  Service Account Name:  prometheus-prometheus-oper-prometheus
  Service Monitor Namespace Selector:
  Service Monitor Selector:
    Match Labels:
      Release:  prometheus
  Version:      v2.16.0
Events:         <none>
```

2. Create a ServerMonitor object with the `release=prometheus` label, e.g. `servicemonitor-exmachina.yaml `
```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  labels:
    spark-role: driver
    release:  prometheus
  name: exmachina-servicemonitor
spec:
  endpoints:
  - interval: 5s
    port: metrics
    path: /metrics
  namespaceSelector:
    matchNames:
    - local-env-k8sns-exmacstandaloneexmachinatestba-01
  selector:
    matchLabels:
      spark-role: driver
```

Troubleshooting
Check service monitor
```
$ kubectl get servicemonitor -n monit
NAME                                                 AGE
exmachina-servicemonitor                             166m

$ kubectl describe servicemonitor  exmachina-servicemonitor -n monit
Name:         exmachina-servicemonitor
Namespace:    monit
Labels:       release=prometheus
              spark-role=driver
Annotations:  <none>
API Version:  monitoring.coreos.com/v1
Kind:         ServiceMonitor
Metadata:
  Creation Timestamp:  2020-06-05T21:50:49Z
  Generation:          1
  Resource Version:    30056
  Self Link:           /apis/monitoring.coreos.com/v1/namespaces/monit/servicemonitors/exmachina-servicemonitor
  UID:                 a2373f8d-01e5-4367-af95-f762e768a8ef
Spec:
  Endpoints:
    Interval:  5s
    Path:      /metrics
    Port:      metrics
  Namespace Selector:
    Match Names:
      local-env-k8sns-exmacstandaloneexmachinatestba-01
  Selector:
    Match Labels:
      Spark - App - Selector:  exmacstandaloneexmachinatestba
      Spark - Role:            driver
Events:                        <none>
```
Check the Service (and also the Pod) and its labels and make sure it does have the same label as configured in the ServiceMonitor selector.
```
$ kubectl get svc --show-labels -n local-env-k8sns-exmacstandaloneexmachinatestba-01
NAME                             TYPE       CLUSTER-IP    EXTERNAL-IP   PORT(S)                                                                        AGE   LABELS
exmacstandaloneexmachinatestba   NodePort   10.102.3.51   <none>        10011:31678/TCP,7077:31372/TCP,10000:31640/TCP,4040:32516/TCP,9091:32306/TCP   15m   Name-0=0local-env-k8ssvc-exmac_2Bstandaloneexmachina_2Btest_2Bba-010,QName-0=0local-env-k8ssvc-exmac_2Bstandaloneexmachina_2Btest_2Bba-01.0,QName-1=0local-01-us-east-1.internal0,c3__cluster-0=0local-env0,c3__created-0=02020-06-06T00_3A24_3A15.476Z0,c3__created_by-0=0BA0,c3__created_from-0=0http_3A_2F_2Flocalhost_3A80800,c3__env-0=0local0,c3__ext_service_name-0=0exmac0,c3__func-0=0k8ssvc0,c3__id-0=0local-env-k8ssvc-exmac_2Bstandaloneexmachina_2Btest_2Bba-010,c3__member-0=0c30,c3__pod-0=0env0,c3__role-0=0exmac_2Bstandaloneexmachina_2Btest_2Bba0,c3__seq-0=0010,c3__tag-0=0test0,c3__tenant-0=0standaloneexmachina0,c3__updated-0=02020-06-06T00_3A24_3A15.476Z0,c3__updated_by-0=0BA0,c3__updated_from-0=0http_3A_2F_2Flocalhost_3A80800,host_name-0=0local-env-k8ssvc-exmac_2Bstandaloneexmachina_2Btest_2Bba-01.0,host_name-1=0local-01-us-east-1.internal0,release=prometheus
```

Add proper label pod
```
$ kubectl label pods  exmacstandaloneexmachinatestba-f86df7c59-qbjlw release=prometheus -n local-env-k8sns-exmacstandaloneexmachinatestba-01
```
Add proper label service
```
$ kubectl label svc exmacstandaloneexmachinatestba release=prometheus -n local-env-k8sns-exmacstandaloneexmachinatestba-01
$ kubectl label svc exmacstandaloneexmachinatestba spark-role=driver -n local-env-k8sns-exmacstandaloneexmachinatestba-01
service/exmacstandaloneexmachinatestba labeled
```

- https://sysdig.com/blog/prometheus-metrics/
- https://sysdig.com/blog/kubernetes-monitoring-prometheus-operator-part3/
- https://docs.couchbase.com/operator/current/tutorial-prometheus.html
- https://levelup.gitconnected.com/building-kubernetes-apps-with-custom-scaling-a-gentle-introduction-a332d7ebc795
- https://medium.com/@zhimin.wen/custom-prometheus-metrics-for-apps-running-in-kubernetes-498d69ada7aa
- https://argus-sec.com/monitoring-spark-prometheus/
- https://stackoverflow.com/questions/49488956/monitoring-apache-spark-with-prometheus
- https://medium.com/@salohyprivat/monitor-spark-streaming-with-prometheus-5b0eff5e318d
- https://www.slideshare.net/databricks/scalable-monitoring-using-prometheus-with-apache-spark-clusters-with-diane-feddema-and-zak-hassan
- https://banzaicloud.com/blog/spark-prometheus-sink-labels/
- https://banzaicloud.com/blog/spark-monitoring/

