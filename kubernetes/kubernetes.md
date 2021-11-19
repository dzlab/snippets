
Switch context
```
$ kubectl config get-contexts 
CURRENT   NAME                        CLUSTER                     AUTHINFO                                                      NAMESPACE
*         docker-desktop              docker-desktop              docker-desktop                                                
          kube-01                     kube-01                     user    

$ kubectl config set current-context MY-CONTEXT
Property "current-context" set.
```
Otherwise use [kubectx](https://github.com/ahmetb/kubectx)

## Azure
Define variable environment
```
export name=dev-azaks-01
export resource=dev-azrg-01
```
Create cluster
```
az aks create --resource-group $resource --name $name --node-count 1 --enable-addons monitoring --generate-ssh-keys
```
Download credentials
```
$ az aks get-credentials --resource-group $resource --name $name
Merged "dev-azaks-01" as current context in /Users/dzlab/.kube/config
```
Check the node
```
$ kubectl get nodes
NAME                                STATUS   ROLES   AGE    VERSION
aks-nodepool1-30349469-vmss000000   Ready    agent   3m4s   v1.20.9
```
https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough
