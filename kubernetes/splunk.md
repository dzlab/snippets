# Splunk

## Setup AKS
See https://github.com/dzlab/snippets/tree/master/tracing-demo/k8s#setup-aks

## Setup Splunk
### Install Splunk Operator
Install Splunk Operator
```
$ kubectl apply -f https://github.com/splunk/splunk-operator/releases/download/1.0.2/splunk-operator-install.yaml
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
$ kubectl get pods
NAME                              READY   STATUS    RESTARTS   AGE
splunk-operator-f7c8d94f9-tsp9z   1/1     Running   0          10s
```

### Install Splunk Standalone
Create a Splunk Standalone deployment
```
$ cat <<EOF | kubectl apply -f -
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
$ kubectl get pods              
NAME                                  READY   STATUS    RESTARTS   AGE
splunk-default-monitoring-console-0   1/1     Running   0          3m19s
splunk-operator-f7c8d94f9-tsp9z       1/1     Running   0          6m38s
splunk-s1-standalone-0                1/1     Running   0          5m56s
```

Get the credentials created for the Splunk Standalone deployment
```
$ kubectl get secret splunk-default-secret -o yaml
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
$ kubectl get secret splunk-default-secret -o go-template=' {{range $k,$v := .data}}{{printf "%s: " $k}}{{if not $v}}{{$v}}{{else}}{{$v | base64decode}}{{end}}{{"\n"}}{{end}}'
 hec_token: 7CD040D8-0744-D8D7-5548-988765A6C806
idxc_secret: SpGYHlKYHj7WDZl8Y1qXuP42
pass4SymmKey: MKgf5NMvaPK8ZqSC74WEvKhn
password: ARDpFz9lu8rDnyv22eSApL8a
shc_secret: OV1wzxliMe2dpFd78l9TWnoS
```
For instance to get the password
```
$ kubectl get secret splunk-default-secret -o go-template='{{ index .data "password" }}' | base64 -d
ARDpFz9lu8rDnyv22eSApL8a
```

Open a connection to Splunk
```
$ kubectl port-forward splunk-s1-standalone-0 8000
Forwarding from 127.0.0.1:8000 -> 8000
Forwarding from [::1]:8000 -> 8000
```

## Setup Splunk Connect
### Create a configuration file
Get Splunk credentials
```
$ hostname="splunk-s1-standalone-service"
$ token=`kubectl get secret splunk-default-secret -o go-template='{{ index .data "hec_token" }}' | base64 -d`
$ password=`kubectl get secret splunk-default-secret -o go-template='{{ index .data "password" }}' | base64 -d`
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

### Install Splunk Connect with Helm
```
$ helm repo add splunk https://splunk.github.io/splunk-connect-for-kubernetes/
"splunk" has been added to your repositories
$ helm install splunkconnect -n splunk -f "${file}" splunk/splunk-connect-for-kubernetes
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
$ helm list -n splunk
NAME         	NAMESPACE	REVISION	UPDATED                                	STATUS  	CHART                              	APP VERSION
splunkconnect	splunk   	2       	2021-08-13 16:42:46.653713878 +0000 UTC	deployed	splunk-connect-for-kubernetes-1.4.7	1.4.7      
$ helm delete splunkconnect -n splunk || true
release "splunkconnect" uninstalled
```

## Resources
- Getting Started with the Splunk Operator for Kubernetes - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/README.md)
- Reading global kubernetes secret object - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/Examples.md#reading-global-kubernetes-secret-object)
- Configuring Ingress to make Splunk ports accessible outside of Kubernetes - [link](https://github.com/splunk/splunk-operator/blob/develop/docs/Ingress.md)
- Splunk Connect for Kubernetes - [link](https://github.com/splunk/splunk-connect-for-kubernetes)
