## Networking
Different ways to expose traffic to a service running inside kubernetes https://medium.com/google-cloud/kubernetes-nodeport-vs-loadbalancer-vs-ingress-when-should-i-use-what-922f010849e0
Connecting Applications with Services https://kubernetes.io/docs/concepts/services-networking/connect-applications-service/

### Ingress
Ingress nginx installation
```
$ helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
$ helm install ingress-nginx ingress-nginx/ingress-nginx -n monitoring
```

Create a nginx ingress service
```
$ kubectl apply -f ingress.yaml -n monitoring
```

If after this, visiting http://localhost/ cannot be resolved then redeploy ingress-nginx chart and do (see https://github.com/kubernetes/ingress-nginx/issues/4360)
```
$ kubectl delete validatingwebhookconfiguration ingress-nginx-admission -n monitoring
```

#### Troubleshooting
See https://kubernetes.github.io/ingress-nginx/troubleshooting/
Check the status of the backend services
```
$ kubectl get ingress ingress-monit -n monitoring
$ kubectl describe ingress ingress-monit -n monitoring
```
Access logs
```
$ kubectl get pods -n monitoring
NAME                                        READY     STATUS    RESTARTS   AGE
nginx-ingress-controller-67956bf89d-fv58j   1/1       Running   0          1m

$ kubectl logs -n monitoring nginx-ingress-controller-67956bf89d-fv58j
```

References:
- https://blog.heptio.com/on-securing-the-kubernetes-dashboard-16b09b1b7aca
- https://docs.giantswarm.io/guides/advanced-ingress-configuration/
- https://matthewpalmer.net/kubernetes-app-developer/articles/kubernetes-ingress-guide-nginx-example.html
- https://kubernetes.io/docs/concepts/services-networking/ingress/
- https://blog.donbowman.ca/2018/09/06/accessing-a-service-in-a-different-namespace-from-a-single-ingress-in-kubernetes/
- Visuals https://medium.com/swlh/kubernetes-services-simply-visually-explained-2d84e58d70e5

## AKS

https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough
https://docs.microsoft.com/en-us/azure/aks/kubernetes-walkthrough-portal

```
$ az login
$ az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

Dashboard: https://docs.microsoft.com/en-us/azure/aks/kubernetes-dashboard

Spark / Scala reportor:
- https://leaks.wanari.com/2019/04/08/gradle-kamon-prometheus-a-complete-guide

