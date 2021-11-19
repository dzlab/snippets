
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

### Azure Files Volume
Create ADLS
```
STORAGE_ACCOUNT_NAME=devadls01
RESOURCE_GROUP=dev-azrg-01
LOCATION=westus
STORAGE_SHARE_NAME=devaksshare
```
Create a storage account
```
az storage account create -n $STORAGE_ACCOUNT_NAME -g $RESOURCE_GROUP -l $LOCATION --sku Standard_LRS
```

Export the connection string as an environment variable, this is used when creating the Azure file share
```
export STORAGE_CONNECTION_STRING=$(az storage account show-connection-string -n $STORAGE_ACCOUNT_NAME -g $RESOURCE_GROUP -o tsv)
```
Create the file share
```
az storage share create -n $STORAGE_SHARE_NAME --connection-string $STORAGE_CONNECTION_STRING
```
Get storage account key
```
STORAGE_KEY=$(az storage account keys list --resource-group $RESOURCE_GROUP --account-name $STORAGE_ACCOUNT_NAME --query "[0].value" -o tsv)
```
Echo storage account name and key
```
echo Storage account name: $STORAGE_ACCOUNT_NAME
echo Storage account key: $STORAGE_KEY
```

https://docs.microsoft.com/en-us/azure/aks/azure-files-volume
