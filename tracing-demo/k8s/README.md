Login to Azure portal
```
$ az login
```

Create a resource group
```
$ az group create --name test-dzlab-azrg-01 --location westus
/subscriptions/xyz/resourceGroups/test-dzlab-azrg-01	westus	None	test-dzlab-azrg-01		None	Microsoft.Resources/resourceGroups
```

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

Push the image to the Container Registery
```
$ docker build -t dzlab/tracing-demo .
$ docker image tag dzlab/tracing-demo:latest dzlabacr01.azurecr.io/dzlab/tracing-demo:latest
$ docker push dzlabacr01.azurecr.io/dzlab/tracing-demo:latest
```

Deploy the application
```
$ kubectl apply -f eshop.yaml
```

Check deployment was successfull
```
$ kubectl get pods
NAME                     READY   STATUS    RESTARTS   AGE
eshop-59d84469f8-8kd54   1/1     Running   0          12s
```

Delete the cluster
```
$ az group delete --name test-dzlab-azrg-01 --yes --no-wait
```

Resources:
- Deploy an Azure Kubernetes Service cluster using the Azure CLI - [link](https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough)
- Authenticate with Azure Container Registry from Azure Kubernetes Service - [link](https://docs.microsoft.com/en-us/azure/aks/cluster-container-registry-integration)
- Push your first image to your Azure container registry using the Docker CLI - [link](https://docs.microsoft.com/en-us/azure/container-registry/container-registry-get-started-docker-cli)