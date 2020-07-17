Splunk on Docker:
- https://splunk.github.io/docker-splunk/


Splunk HTTP Event Collector:
- https://www.function1.com/2017/02/using-http-event-collector-and-splunk-logging-driver-and-to-gain-visibility-into-your-docker
- https://www.outcoldsolutions.com/docs/monitoring-docker/v5/splunk-output/

Kubernetes:
- Logging Architecture https://kubernetes.io/docs/concepts/cluster-administration/logging/#cluster-level-logging-architectures
- https://stackoverflow.com/questions/50639744/forwarding-logs-from-kubernetes-to-splunk
- https://community.splunk.com/t5/Getting-Data-In/How-can-we-log-and-containerize-the-logs-using-Kubernetes-and/td-p/357069


## Book: 9781838981747-IMPROVING_YOUR_SPLUNK_SKILLS.pdf
> Using the Universal Forwarder to gather data (page 399)
> When the data we want to collect is not located directly on the server where Splunk is installed, the Splunk Universal Forwarder (UF) can be installed on your remote endpoint servers and used to forward data back to Splunk to be indexed. The Universal Forwarder is like the Splunk server in that it has many of the same features, but it does not contain Splunk web and doesn't come bundled with the Python executable and libraries. Additionally, the Universal Forwarder cannot process data in advance, such as performing line breaking and timestamp extraction.

> How it works...
> When you tell the forwarder which server to send data to, you basically add a new configuration stanza into an outputs.conf file behind the scenes. On the Splunk server, an inputs.conf file will contain a [splunktcp] stanza to enable receiving. The outputs.conf file on the Splunk forwarder will be located in $SPLUNK_HOME/etc/system/local, and the inputs.conf file on the Splunk server will be located in the local directory of the app you were in (the launcher app in this case) when configuring receiving.
> Using forwarders to collect and forward data has many advantages. The forwarders communicate with the indexers on TCP port 9997 by default, which makes for a very simple set of firewall rules that need to be opened. Forwarders can also be configured to load balance their data across multiple indexers, increasing search speeds and availability. Additionally, forwarders can be configured to queue the data they collect if communication with the indexers is lost. This can be extremely important when collecting data that is not read from logfiles, such as performance counters or syslog streams, as the data cannot be re-read.


> Receiving data using the HTTP Event Collector (page 406)
> How it works...
> To get the HEC to work, you firstly configured a few global settings. These included the default index, default source type, and the HTTP port that Splunk will listen on. These default values, such as index and source type, will be used by the HEC, unless the data itself contains the specific values to use. The port commonly used for the HEC is port 8088. This single port can receive multiple different types of data since it is all differentiated by the token that is passed with it and by interpreting the data within the payload of the request.
> After configuring the defaults, you then generated a new token, specifically for the inventory scanner data. You provided a specific source type for this data source and selected the index that the data should go to. These values will override the defaults and help to ensure that data is routed to the correct index.
The HEC is now up and running and listening on port 8088 for the inventory scan HTTP data to be sent to it.


> HTTP Event Collector (HEC) - HTTP requests with a custom JSON object
> The HTTP Event Collector is a highly efficient and secure way to get data into Splunk over HTTP/HTTPS from devices that don't need, or are unable to run, the Splunk Universal Forwarder. This is especially relevant to the growing Internet of Things (IoT) market. 
> The HTTP Event Collector is easy to configure and can run on any Splunk instance. It utilizes tokens for authentication, which means you will never need to put credentials into the sending application.
> OK, let's get a hands-on experience of this exciting technology!


> To set up the HTTP Event Collector for a specific data input, you needed to create a token. When setting up the token, you defined a default index and default sourcetype. These values will be used unless the data itself contains the values to use. The set of indexes that can be used by that token also have to be specified, so that someone cannot craft a custom event that could be routed into the wrong index.
> Finally, you simulated the sending of an event using the Linux curl utility. You specified the token in an authorization header and the data to be posted as a JSON object. The data passed in the JSON object is what Splunk will interpret as the data for the event.

## Splunk Operator
Install Splunk Operator `kubectl apply -f http://tiny.cc/splunk-operator-install`

Setup a Splunk deployment `kubectl apply -f splunk-enterprise.yaml` using following:
```yaml
apiVersion: enterprise.splunk.com/v1alpha2
kind: Standalone
metadata:
  name: s1
  finalizers:
  - enterprise.splunk.com/delete-pvc
```

Get the passowrd
```bash
$ kubectl get secret splunk-s1-standalone-secrets -o jsonpath='{.data.password}' | base64 --decode
```
Check Splunk deplyment state (it may take couple minutes before it becomes `Running`)
```
$ kubectl get pods
NAME                                                     READY   STATUS              RESTARTS   AGE
splunk-s1-standalone-0                                   0/1     ContainerCreating   0          88s
. . .
```
Login to Splunk
```
$ kubectl port-forward splunk-s1-standalone-0 8000
```

HEC:
* AKS DEV: `2c293eb0-dba7-4700-b7ee-74fef6394d05`
* Docker Desktop: `f072b3e0-8255-4e52-9d02-2b717ae5137e`


```bash
$ helm install splunk-connect-daemonset -f metrics_values.yaml https://github.com/splunk/splunk-connect-for-kubernetes/releases/download/1.4.1/splunk-connect-for-kubernetes-1.4.1.tgz
```

Update HEC config
```bash
$ helm install splunk-connect-daemonset \
        --set global.splunk.hec.host=prd-p-kd9fn.splunkcloud.com \
        --set global.splunk.hec.token=3fc9e657-d7de-4f8b-86ee-72fe175c1fd2 \
        --set global.splunk.hec.port=8088 \
        --set global.splunk.hec.protocol=https \
        --set global.splunk.hec.insecureSSL=true \
        --set splunk-kubernetes-logging.splunk.hec.indexName=k8s-logs \
        --set splunk-kubernetes-metrics.splunk.hec.indexName=k8s-metrics \
        --set splunk-kubernetes-objects.splunk.hec.indexName=k8s-meta \
        https://github.com/splunk/splunk-connect-for-kubernetes/releases/download/1.4.1/splunk-connect-for-kubernetes-1.4.1.tgz

$ helm upgrade splunk-connect-daemonset \
        --set global.splunk.hec.host=splunk-s1-standalone-headless \
        --set global.splunk.hec.token=f072b3e0-8255-4e52-9d02-2b717ae5137e \
        https://github.com/splunk/splunk-connect-for-kubernetes/releases/download/1.4.1/splunk-connect-for-kubernetes-1.4.1.tgz
```
Update index name
```bash
$ helm upgrade splunk-connect-daemonset \
        --set splunk-kubernetes-metrics.splunk.hec.indexName=default \
        https://github.com/splunk/splunk-connect-for-kubernetes/releases/download/1.4.1/splunk-connect-for-kubernetes-1.4.1.tgz
```

Use the following search queries:
- `source="http:exmac-token" (index="default") sourcetype="log4j"`
- `source="http:splunk-connect-hec"`

Curling
```
$ curl -k "https://prd-p-kd9fn.splunkcloud.com:8088/services/collector" \
    -H "Authorization: Splunk 3fc9e657-d7de-4f8b-86ee-72fe175c1fd2" \
    -d '{"event": "Hello, world!", "sourcetype": "manual"}'
```

Under the hood, the objects logging uses [kubeclient](https://github.com/abonas/kubeclient) ruby k8s client.

Reference:
- Splunk Operator [link](https://splunk.github.io/splunk-operator/)
- headless k8s service [link](https://medium.com/faun/kubernetes-headless-service-vs-clusterip-and-traffic-distribution-904b058f0dfd)
- Splunk Connect for Kubernetes on EKS! [link](https://www.splunk.com/en_us/blog/partners/splunk-connect-for-kubernetes-on-eks.html)
- Use cURL to manage HTTP Event Collector tokens, events, and services [link](https://docs.splunk.com/Documentation/Splunk/8.0.4/Data/HTTPEventCollectortokenmanagement)
- The Complete Guide to Kubernetes Logging [link](https://sematext.com/guides/kubernetes-logging/)
- A Practical Guide to Kubernetes Logging [link](https://logz.io/blog/a-practical-guide-to-kubernetes-logging/)
