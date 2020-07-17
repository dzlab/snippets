### Setup k8s metrics-server
#### Minikube
https://kubernetes.io/docs/tutorials/hello-minikube/
Minikube has a set of built-in addo-ns that can be enabled/disabled, you can view them
```
$ minikube addons list
|-----------------------------|----------|--------------|
|         ADDON NAME          | PROFILE  |    STATUS    |
|-----------------------------|----------|--------------|
| dashboard                   | minikube | enabled ✅   |
| default-storageclass        | minikube | enabled ✅   |
| efk                         | minikube | disabled     |
| freshpod                    | minikube | disabled     |
| gvisor                      | minikube | disabled     |
| helm-tiller                 | minikube | disabled     |
| ingress                     | minikube | disabled     |
| ingress-dns                 | minikube | disabled     |
| istio                       | minikube | disabled     |
| istio-provisioner           | minikube | disabled     |
| logviewer                   | minikube | disabled     |
| metrics-server              | minikube | disabled     |
| nvidia-driver-installer     | minikube | disabled     |
| nvidia-gpu-device-plugin    | minikube | disabled     |
| registry                    | minikube | disabled     |
| registry-aliases            | minikube | disabled     |
| registry-creds              | minikube | disabled     |
| storage-provisioner         | minikube | enabled ✅   |
| storage-provisioner-gluster | minikube | disabled     |
|-----------------------------|----------|--------------|
```
The metrics server is one of those addons, but default it is desabled. You can enable it with:
$ minikube addons enable metrics-server
#### k8s
see https://blog.codewithdan.com/enabling-metrics-server-for-kubernetes-on-docker-desktop/
```
$ git clone https://github.com/kubernetes-sigs/metrics-server.git
$ cd metrics-server
$ kubectl create -f deploy/1.8+/
```
#### helm
Create a namespace where the metrics-server will be running
```
$ kubectl create namespace monitoring
```
Install metrics-server using helm in the `monitoring` namespace.
```
$ helm install metrics-server stable/metrics-server --namespace monitoring --set args={"--kubelet-insecure-tls=true,--kubelet-preferred-address-types=InternalIP\,Hostname\,ExternalIP"}
```

Now you can check the metrics-server is running with
```
$ kubectl get pods --all-namespaces | grep metrics-server
kube-system            metrics-server-7bc6d75975-9bkvh              1/1     Running   0          24m
https://www.datadoghq.com/blog/how-to-collect-and-graph-kubernetes-metrics/
```
