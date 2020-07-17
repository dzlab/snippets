### Access dashboard
#### Minikube dashboard
https://medium.com/@kari.marttila/exploring-kubernetes-with-minikube-c90c60b25e81
$ minikube dashboard
A URL like the following will be opened http://127.0.0.1:51250/api/v1/namespaces/kubernetes-dashboard/services/http:kubernetes-dashboard:/proxy/#/overview?namespace=default

#### k8s UI
Follow the steps here:
- Main resource: https://www.replex.io/blog/the-ultimate-guide-to-the-kubernetes-dashboard-how-to-install-and-integrate-metrics-server
- Good to read : https://kubernetes.io/docs/tasks/access-application-cluster/web-ui-dashboard/

```
$ kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.0.0-beta8/aio/deploy/recommended.yaml
```
Install k8s UI with helm
```
$ helm install kubernetes-dashboard stable/kubernetes-dashboard -n monitoring
```


To access the dashboard we need to authenticate using an access token (it's also possible to use kubeconfig) that we can get as follows:

1. Create a new service account for the dashboard
```
$ kubectl create serviceaccount dashboard-admin-sa
```
2. Bind the dashboard-admin-sa service account to the cluster-admin role
```
$ kubectl create clusterrolebinding dashboard-admin-sa --clusterrole=cluster-admin --serviceaccount=default:dashboard-admin-sa
```
3. List secrets to find the actual name of the `dashboard-admin-sa` service account
```
$ kubectl get secrets
NAME                             TYPE                                  DATA   AGE
dashboard-admin-sa-token-bmsj6   kubernetes.io/service-account-token   3      21s
default-token-vjhhs              kubernetes.io/service-account-token   3      60d
local-env-k8ssec                 Opaque                                0      13d
```
4. Get the access token:
```
$ kubectl describe secret dashboard-admin-sa-token-bmsj6
```
Alternatively, Generate a bearer token, otherwise create a user as explained here https://github.com/kubernetes/dashboard/blob/master/docs/user/access-control/creating-sample-user.md
```
$ kubectl -n kubernetes-dashboard describe secret $(kubectl -n kubernetes-dashboard get secret | grep admin-user | awk '{print $1}')
```
Proxy traffic to the UI (default port is 8001)
```
$ kubectl proxy
$ kubectl proxy --port=8080
```
Now you can access the UI through a URL that looks this: http://localhost:8080/api/v1/proxy/namespaces/<NAMESPACE>/services/<SERVICE-NAME>:<PORT-NAME>/
e.g. http://localhost:8001/api/v1/namespaces/kubernetes-dashboard/services/https:kubernetes-dashboard:/proxy/#/error?namespace=default

Resource https://www.replex.io/blog/how-to-install-access-and-add-heapster-metrics-to-the-kubernetes-dashboard
