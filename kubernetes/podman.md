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

## Resources
- https://marcusnoble.co.uk/2021-09-01-migrating-from-docker-to-podman/
- https://github.com/heyvito/podman-macos
- https://www.danielstechblog.io/running-podman-on-macos-with-multipass/
