# Podman

```
brew install podman
```

Create a virtual machine for Podman to run from:
```
$ podman machine init
Downloading VM image: fedora-coreos-35.20210924.1.0-qemu.x86_64.qcow2.xz: done  
Extracting compressed file
```

Start the virtual machine and set up the connection to Podman:
```
$ podman machine start
```

Check machine status
```
$ podman machine ls
NAME                     VM TYPE     CREATED      LAST UP
podman-machine-default*  qemu        2 hours ago  2 hours ago
```

Delete machine
```
$ podman machine rm podman-machine-default

The following files will be deleted:

/Users/dzlab/.ssh/podman-machine-default
/Users/dzlab/.ssh/podman-machine-default.pub
/Users/dzlab/.config/containers/podman/machine/qemu/podman-machine-default.ign
/Users/dzlab/.local/share/containers/podman/machine/qemu/podman-machine-default_fedora-coreos-35.20210924.1.0-qemu.x86_64.qcow2
/Users/dzlab/.config/containers/podman/machine/qemu/podman-machine-default.json


Are you sure you want to continue? [y/N] y
```

## Resources
- https://marcusnoble.co.uk/2021-09-01-migrating-from-docker-to-podman/
- https://github.com/heyvito/podman-macos
- https://www.danielstechblog.io/running-podman-on-macos-with-multipass/
