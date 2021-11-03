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
