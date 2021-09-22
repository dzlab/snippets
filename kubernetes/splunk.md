# Splunk

## Setup AKS
See https://github.com/dzlab/snippets/tree/master/tracing-demo/k8s#setup-aks

## Setup Splunk
### Install Splunk Operator
Install Splunk Operator
```
$ kubectl apply -f https://github.com/splunk/splunk-operator/releases/download/1.0.2/splunk-operator-install.yaml -n monit
customresourcedefinition.apiextensions.k8s.io/clustermasters.enterprise.splunk.com created
customresourcedefinition.apiextensions.k8s.io/indexerclusters.enterprise.splunk.com created
customresourcedefinition.apiextensions.k8s.io/licensemasters.enterprise.splunk.com created
customresourcedefinition.apiextensions.k8s.io/searchheadclusters.enterprise.splunk.com created
customresourcedefinition.apiextensions.k8s.io/standalones.enterprise.splunk.com created
serviceaccount/splunk-operator created
role.rbac.authorization.k8s.io/splunk:operator:namespace-manager created
rolebinding.rbac.authorization.k8s.io/splunk:operator:namespace-manager created
deployment.apps/splunk-operator created
```

Check the operator is up and running
```
$ kubectl get pods -n monit
NAME                              READY   STATUS    RESTARTS   AGE
splunk-operator-f7c8d94f9-tsp9z   1/1     Running   0          10s
```

### Install Splunk Standalone
Create a Splunk Standalone deployment
```
$ cat <<EOF | kubectl apply -n monit -f -
apiVersion: enterprise.splunk.com/v2
kind: Standalone
metadata:
  name: s1
  finalizers:
  - enterprise.splunk.com/delete-pvc
EOF
standalone.enterprise.splunk.com/s1 created
```
Check all Splunk Pods are up and running
```
$ kubectl get pods -n monit              
NAME                                  READY   STATUS    RESTARTS   AGE
splunk-default-monitoring-console-0   1/1     Running   0          3m19s
splunk-operator-f7c8d94f9-tsp9z       1/1     Running   0          6m38s
splunk-s1-standalone-0                1/1     Running   0          5m56s
```

Get the credentials created for the Splunk Standalone deployment
```
$ kubectl get secret splunk-default-secret -o yaml -n monit
apiVersion: v1
data:
  hec_token: N0NEMDQwRDgtMDc0NC1EOEQ3LTU1NDgtOTg4NzY1QTZDODA2
  idxc_secret: U3BHWUhsS1lIajdXRFpsOFkxcVh1UDQy
  pass4SymmKey: TUtnZjVOTXZhUEs4WnFTQzc0V0V2S2hu
  password: QVJEcEZ6OWx1OHJEbnl2MjJlU0FwTDhh
  shc_secret: T1Yxd3p4bGlNZTJkcEZkNzhsOVRXbm9T
kind: Secret
metadata:
  creationTimestamp: "2021-08-25T17:32:03Z"
  managedFields:
  - apiVersion: v1
    fieldsType: FieldsV1
    fieldsV1:
      f:data:
        .: {}
        f:hec_token: {}
        f:idxc_secret: {}
        f:pass4SymmKey: {}
        f:password: {}
        f:shc_secret: {}
      f:metadata:
        f:ownerReferences:
          .: {}
          k:{"uid":"3ba7943f-b283-452d-9917-02ebb7f7d114"}:
            .: {}
            f:apiVersion: {}
            f:controller: {}
            f:kind: {}
            f:name: {}
            f:uid: {}
      f:type: {}
    manager: splunk-operator
    operation: Update
    time: "2021-08-25T17:32:03Z"
  name: splunk-default-secret
  namespace: default
  ownerReferences:
  - apiVersion: enterprise.splunk.com/v2
    controller: false
    kind: Standalone
    name: s1
    uid: 3ba7943f-b283-452d-9917-02ebb7f7d114
  resourceVersion: "851"
  uid: 15ed8cc4-6af0-438d-8568-0b096454c2f1
type: Opaque
```

Decode the secrents from Base64
```
$ kubectl get secret splunk-monit-secret -n monit -o go-template=' {{range $k,$v := .data}}{{printf "%s: " $k}}{{if not $v}}{{$v}}{{else}}{{$v | base64decode}}{{end}}{{"\n"}}{{end}}'
 hec_token: 7CD040D8-0744-D8D7-5548-988765A6C806
idxc_secret: SpGYHlKYHj7WDZl8Y1qXuP42
pass4SymmKey: MKgf5NMvaPK8ZqSC74WEvKhn
password: ARDpFz9lu8rDnyv22eSApL8a
shc_secret: OV1wzxliMe2dpFd78l9TWnoS
```
For instance to get the password
```
$ kubectl get secret splunk-monit-secret -n monit -o go-template='{{ index .data "password" }}' | base64 -d
ARDpFz9lu8rDnyv22eSApL8a
```

### Access Splunk
#### Port forwarding
Open a connection to Splunk via **Port forwarding**
```
$ kubectl port-forward splunk-s1-standalone-0 8000 -n monit
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
```

#### Ingress
Open a connection to Splunk via **Ingress**

Create an Ingress controller manifest `splunk-ingress.yaml` that will forward requests to `splunk-s1-standalone-service` backend service.
```
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: splunk-ingress
  annotations:
    # use the shared ingress-nginx
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/default-backend: splunk-s1-standalone-service
    nginx.ingress.kubernetes.io/proxy-body-size: "0"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "600"
spec:
  rules:
  - http:
      paths:
      - path: "/splunk"
        pathType: Prefix
        backend:
          service:
            name: splunk-s1-standalone-service
            port:
              number: 8000
```

```
$ kubectl apply -f splunk-ingress.yaml -n monit
```

```
$ kubectl get ingress splunk-ingress -n monit        
NAME                 CLASS    HOSTS   ADDRESS   PORTS   AGE
ingress-standalone   <none>   *                 80      118s
```

```
$ kubectl get ingress splunk-ingress -n monit -o yaml
```

#### Load Balancer
Create a load balancer manifest `splunk-lb.yaml`
```
apiVersion: v1
kind: Service
metadata:
  name: splunk-lb
spec:
  type: LoadBalancer
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  selector:
    app.kubernetes.io/component: standalone
    app.kubernetes.io/instance: splunk-s1-standalone
    app.kubernetes.io/managed-by: splunk-operator
    app.kubernetes.io/name: standalone
    app.kubernetes.io/part-of: splunk-s1-standalone
```
Create load balancer service
```
$ kubectl apply -f splunk-lb.yaml -n monit
```
Check external IP
```
$ kubectl get svc splunk-lb -n monit -o wide
NAME        TYPE           CLUSTER-IP     EXTERNAL-IP    PORT(S)        AGE   SELECTOR
splunk-lb   LoadBalancer   INT-IP-ADDR    EXT-IP-ADDR    80:32656/TCP   91s   app.kubernetes.io/component=standalone,app.kubernetes.io/instance=splunk-s1-standalone,app.kubernetes.io/managed-by=splunk-operator,app.kubernetes.io/name=standalone,app.kubernetes.io/part-of=splunk-s1-standalone
```


## Setup Splunk Connect
### Create a configuration file
Get splunk server address, use DNS name `<service>.<namespace>` or just `<service>`
```
$ hostname="splunk-s1-standalone-service"
```

Get Splunk credentials
```
$ token=`kubectl get secret splunk-monit-secret -n monit -o go-template='{{ index .data "hec_token" }}' | base64 -d`
$ password=`kubectl get secret splunk-monit-secret -n monit -o go-template='{{ index .data "password" }}' | base64 -d`
$ index="main"
$ file=$(mktemp /tmp/splunk-connect-values.XXXXXX)
```

Define a values file specific to our Splunk deployment (for more options see default Splunk Connect [values.yaml](https://github.com/splunk/splunk-connect-for-kubernetes/blob/develop/helm-chart/splunk-connect-for-kubernetes/values.yaml) file).

Custom values file for collecting logs
```
$ cat >"${file}" << EOF
global:
  splunk:
    hec:
      host: ${hostname}
      port: 8088
      token: ${token}
      protocol: https
      indexName: ${index}
      insecureSSL: true

splunk-kubernetes-logging:
  enabled: true
splunk-kubernetes-objects:
  enabled: false
splunk-kubernetes-metrics:
  enabled: false
EOF
```
Note by default the expected log format is JSON, so if your containers output text you may need to configure the format accordingly, e.g.
```
$ cat >"${file}" << EOF
global:
  splunk:
    hec:
      host: ${hostname}
      port: 8088
      token: ${token}
      protocol: https
      indexName: ${index}
      insecureSSL: true

splunk-kubernetes-logging:
  enabled: true
  containers:
    logFormat: '%Y-%m-%dT%H:%M:%S.%N%:z'
    logFormatType: cri
  logs:
    applogs:
      from:
        pod: '*'
      multiline:
        firstline: /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[-+]\d{4}/
        separator: ""

splunk-kubernetes-objects:
  enabled: false
splunk-kubernetes-metrics:
  enabled: false
EOF
```

Custom values file for collecting logs, metrics, objects
```
$ cat >"${file}" << EOF
global:
  splunk:
    hec:
      host: ${hostname}
      port: 8088
      token: ${token}
      protocol: https
      indexName: ${index}
      insecureSSL: true
splunk-kubernetes-logging:
  enabled: true
  splunk:
    hec:
      host: ${hostname}
      port: 8088
      token: ${token}
      protocol: https
      indexName: ${index}
      insecureSSL: true
splunk-kubernetes-objects:
  enabled: true
  splunk:
    hec:
      host: ${hostname}
      token: ${token}
      protocol: https
      indexName: ${index}
      insecureSSL: true
splunk-kubernetes-metrics:
  enabled: false
  splunk:
    hec:
      host: ${hostname}
      port: 8088
      token: ${token}
      protocol: https
      indexName: metrics
      insecureSSL: true
EOF
```

For multiline logs handling check:
- [DOCS] Add multiline logging tutorial - [link](https://github.com/splunk/splunk-connect-for-kubernetes/issues/255)
- Multiline log assistance - [link](https://github.com/splunk/splunk-connect-for-kubernetes/issues/134)
- Splunking Ghost - [link](https://mattymo.io/splunking-ghost/)
- Splunk Toronto UserGroup May 2020 - [link](https://mattymo.io/code/mattymo/splunk_toronto_usergroup_may_2020/-/blob/master/README.md#deploy-splunk-connect-for-kubernetes)

### Install Splunk Connect with Helm
```
$ helm repo add splunk https://splunk.github.io/splunk-connect-for-kubernetes/
"splunk" has been added to your repositories
$ helm install splunkconnect -n monit -f "${file}" splunk/splunk-connect-for-kubernetes
NAME: splunkconnect
LAST DEPLOYED: Wed Aug 25 11:26:37 2021
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
███████╗██████╗ ██╗     ██╗   ██╗███╗   ██╗██╗  ██╗██╗    
██╔════╝██╔══██╗██║     ██║   ██║████╗  ██║██║ ██╔╝╚██╗   
███████╗██████╔╝██║     ██║   ██║██╔██╗ ██║█████╔╝  ╚██╗  
╚════██║██╔═══╝ ██║     ██║   ██║██║╚██╗██║██╔═██╗  ██╔╝  
███████║██║     ███████╗╚██████╔╝██║ ╚████║██║  ██╗██╔╝
╚══════╝╚═╝     ╚══════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝

Listen to your data.

Splunk Connect for Kubernetes is spinning up in your cluster.
After a few minutes, you should see data being indexed in your Splunk.

If you get stuck, we're here to help.
Look for answers here: http://docs.splunk.com

Warning: Disabling TLS will send the data unencrypted and will be vulnerable to MiTM attacks
```

After successfully deploying Splunk Connect an index called `main` will be created
![image](https://user-images.githubusercontent.com/1645304/130860343-7e689d7f-04b2-4a40-852a-0d3085c88138.png)


### Search the logs
Check logs are forwarded to splunk
```
$ url="localhost"
$ echo "To login use admin:${password} http://${url}:8000"
```

![image](https://user-images.githubusercontent.com/1645304/130846001-aa36c09e-9e96-43de-a566-9b5185f43082.png)

### Clean up
```
$ helm list -n monit
NAME         	NAMESPACE	REVISION	UPDATED                                	STATUS  	CHART                              	APP VERSION
splunkconnect	splunk   	2       	2021-08-13 16:42:46.653713878 +0000 UTC	deployed	splunk-connect-for-kubernetes-1.4.7	1.4.7      
$ helm delete splunkconnect -n monit || true
release "splunkconnect" uninstalled
```

## Resources
- Getting Started with the Splunk Operator for Kubernetes - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/README.md)
- Reading global kubernetes secret object - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/Examples.md#reading-global-kubernetes-secret-object)
- Configuring Ingress to make Splunk ports accessible outside of Kubernetes - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/Ingress.md)
- Splunk Connect for Kubernetes - [link](https://github.com/splunk/splunk-connect-for-kubernetes)
- Use a public Standard Load Balancer in Azure Kubernetes Service (AKS) - [link](https://docs.microsoft.com/en-us/azure/aks/load-balancer-standard)
- Concat plugin used by Splunk Connect to parse logs - [link](https://github.com/fluent-plugins-nursery/fluent-plugin-concat)
- Use DNS names to refer to a service located in another namespace - [link](https://stackoverflow.com/questions/37221483/service-located-in-another-namespace)
