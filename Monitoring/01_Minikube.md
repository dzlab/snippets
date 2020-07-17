This document describes how to configure a Kubernetes cluster with minikube and setup a monitoring infrastructure with Prometheus and Grafana.

## Install Minikube
- https://kubernetes.io/docs/tasks/tools/install-minikube/
- https://matthewpalmer.net/kubernetes-app-developer/articles/guide-install-kubernetes-mac.html

### Preresuitie:
- Check virtualization is supported on macOS,
`sysctl -a | grep -E --color 'machdep.cpu.features|VMX'`

### Install kubectl
- https://kubernetes.io/docs/tasks/tools/install-kubectl/#install-kubectl-on-macos
`brew install kubectl`

References:
- https://www.sumologic.com/blog/kubectl-logs/

### Install minikube
`brew install minikube`

### Install Hypervisor
- KVM https://www.linuxtechi.com/install-configure-kvm-ubuntu-18-04-server/
You can run minikube on different drivers (Docker, KVM/QEMU, VirtualBox)
On OSX, it is possile to setup QEMU https://graspingtech.com/ubuntu-desktop-18.04-virtual-machine-macos-qemu/
But a much easier option is VirtualBox (but it's the slowest option).
Unfortunately, it is not possile with Docker, as when you start minikube you will see
```
$ minikube start --driver=none
😄  minikube v1.9.2 on Darwin 10.15.4
💣  The driver 'none' is not supported on darwin
```

Install VirtualBox
```
$ brew cask install virtualbox
```

Install KVM on linux/ubuntu https://www.linuxtechi.com/install-configure-kvm-ubuntu-18-04-server/


hyperkit
```
$ brew install hyperkit
```

### Confirm installation
Start minikube using docker k8s (if you're not on OSX)
Note this will not run if you're on Darwin:
minikube start --driver=none
To check all possible drivers you can use
```
$ minikube start --help
```
minikube start --driver=virtualbox
```
➜  ~ minikube start --driver=virtualbox                              
😄  minikube v1.9.2 on Darwin 10.15.4
✨  Using the virtualbox driver based on existing profile
👍  Starting control plane node m01 in cluster minikube
🤷  virtualbox "minikube" VM is missing, will recreate.
🔥  Creating virtualbox VM (CPUs=2, Memory=4000MB, Disk=20000MB) ...
🐳  Preparing Kubernetes v1.18.0 on Docker 19.03.8 ...
🌟  Enabling addons: default-storageclass, storage-provisioner
🏄  Done! kubectl is now configured to use "minikube"
```

With hyperkit (faster than virtualbox)
```
➜  ~ minikube start --driver=hyperkit
```

To stop minikube VM
```
$ minikube stop
✋  Stopping "minikube" in virtualbox ...
🛑  Node "m01" stopped.
```
Alternatively do the following hack:
```
$ minikube ssh
$ sudo poweroff
```

## References:
- https://cheatsheet.dennyzhang.com/cheatsheet-minikube-a4
- https://learnk8s.io/templating-yaml-with-code
- https://osm.etsi.org/wikipub/index.php/OSM9_Hackfest
