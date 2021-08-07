# Kubernetes

## Setup AKS
### Pre install
Login to Azure portal
```
$ az login
```

Create a resource group
```
$ az group create --name test-dzlab-azrg-01 --location westus
/subscriptions/xyz/resourceGroups/test-dzlab-azrg-01	westus	None	test-dzlab-azrg-01		None	Microsoft.Resources/resourceGroups
```
### Install
Create a Kubernetes service
```
$ az aks create --resource-group test-dzlab-azrg-01 --name test-dzlab-azaks-01 --node-count 1 --generate-ssh-keys
```

Download AKS credentials and configure kubectl by modifying `~/.kube/config`
```
$ az aks get-credentials --resource-group test-dzlab-azrg-01 --name test-dzlab-azaks-01
Merged "test-dzlab-azaks-01" as current context in /Users/dzlab/.kube/config
```
Check access to the created Kubernetes with `kubectl`
```
$ kubectl get nodes
NAME                                STATUS   ROLES   AGE     VERSION
aks-nodepool1-12345678-vmss000000   Ready    agent   4m12s   v1.20.7
```
### Teardown
Delete the cluster
```
$ az group delete --name test-dzlab-azrg-01 --yes --no-wait
```

## Setup Container Registery
Create an Azure Container Registry which will be availble at dzlabacr01.azurecr.io
```
$ az acr create -n dzlabACR01 -g test-dzlab-azrg-01 --sku basic
Falsenis2021-08-06T02:42:59.318585+00:00	False	0		/subscriptions/subscriptionID/resourceGroups/test-dzlab-azrg-01/providers/Microsoft.ContainerRegistry/registries/dzlabACR01	None	westus	dzlabacr01.azurecr.io	dzlabACR01	None		0	Succeeded	Enabled	test-dzlab-azrg-01		None	None			Microsoft.ContainerRegistry/registries
```

Attch the Container Registery to our Kubernetes cluster
```
$ az aks update -n test-dzlab-azaks-01 -g test-dzlab-azrg-01 --attach-acr dzlabACR01
```

Log in to the Container Registery
```
$ az acr login --name dzlabACR01
Login Succeeded
$ docker login dzlabacr01.azurecr.io
```

### Push images
Push the image to the Container Registery
```
$ docker build -t dzlab/tracing-demo .
$ docker image tag dzlab/tracing-demo:latest dzlabacr01.azurecr.io/dzlab/tracing-demo:latest
$ docker push dzlabacr01.azurecr.io/dzlab/tracing-demo:latest
$ docker image tag jaegertracing/all-in-one:1.6 dzlabacr01.azurecr.io/jaegertracing/all-in-one:1.6
$ docker push dzlabacr01.azurecr.io/jaegertracing/all-in-one:1.6
```
## Deploy
Deploy the application
```
$ kubectl apply -f eshop.yaml
```

Check deployment was successfull
```
$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
billing-78c7d6b646-r455k     1/1     Running   0          60s
delivery-68ddb5dccb-vmvdp    1/1     Running   0          60s
eshop-59d84469f8-mcxq5       1/1     Running   0          60s
inventory-6cf44c6fcb-qgfkv   1/1     Running   0          60s
jaeger-6855c88678-twld4      1/1     Running   0          9s
logistics-b5c9c4d74-gtt7x    1/1     Running   0          60s
```

Establish connection from local machine to jaeger service
```
$ kubectl port-forward jaeger-6855c88678-twld4 16686:16686
```

Establish connection from local machine to eshop main service
```
$ kubectl port-forward eshop-59d84469f8-mcxq5 8080:8080
```
## Setup Istio
Deploy the Istio control plane. Please note that we need to enable tracing and set sampling to 100.0 in the mesh options, otherwise, you may not be able to see the traces in the Jaeger UI.
```
$ istioctl x precheck
✔ No issues found when checking the cluster. Istio is safe to install or upgrade!
  To get started, check out https://istio.io/latest/docs/setup/getting-started/
```

Install istio demo profile (good for testing)
```
$ istioctl install --set profile=demo -y
✔ Istio core installed
✔ Istiod installed
✔ Ingress gateways installed
✔ Egress gateways installed
✔ Installation complete
Thank you for installing Istio 1.10.  Please take a few minutes to tell us about your install/upgrade experience!  https://forms.gle/KjkrDnMPByq7akrYA
```

Check what was installed
```
$ kubectl -n istio-system get deploy
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
istio-egressgateway    1/1     1            1           3m33s
istio-ingressgateway   1/1     1            1           3m33s
istiod                 1/1     1            1           3m47s

$ kubectl -n istio-system get IstioOperator installed-state -o yaml
```

```
$ kubectl label namespace default istio-injection=enabled
namespace/default labeled
```

### Install Jager addon
Install Jaeger addon to collect and display the generated traces. Follow instruction in Jaeger installation guide [link](https://istio.io/latest/docs/ops/integrations/jaeger/#installation).
```
$ kubectl apply -f https://raw.githubusercontent.com/istio/istio/release-1.10/samples/addons/jaeger.yaml
deployment.apps/jaeger created
service/tracing created
service/zipkin created
service/jaeger-collector created
```

Enable sidecar injection for the default namespace. Once enabled, Istio will inject an Envoy sidecar into each pod of the application to automatically generate spans for all the inbound and outbound HTTP requests of that pod.
```
$ kubectl label namespace default istio-injection=enabled
error: 'istio-injection' already has a value (enabled), and --overwrite is false
```

## Resources:
- Deploy an Azure Kubernetes Service cluster using the Azure CLI - [link](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough)
- Authenticate with Azure Container Registry from Azure Kubernetes Service - [link](https://docs.microsoft.com/en-us/azure/aks/cluster-container-registry-integration)
- Push your first image to your Azure container registry using the Docker CLI - [link](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli)
- Install with Istioctl - [link](https://istio.io/latest/docs/setup/install/istioctl/)