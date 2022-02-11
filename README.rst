*******
nspctl
*******

nspctl, management tool for systemd-nspawn containers.


Why nspctl?
###########

There are different tools for systemd-nspawn containers. You can use native tools ('machinectl' command) to manage for containers.
But systemd-nspawn, machinectl or other tools do not support non-systemd containers.
(non-systemd containers: containers with another init system from systemd. Such as systemv, openrc, upstart, busybox init, etc.)

nspctl supports containers with any init system. nspctl provides almost all of the features that machinectl provides.

**Currently implemented features are:**

* Lists

  - running containers
  - stopped containers
  - all containers

* Containers info
* Containers status
* Start the container
* Stop the container
* Reboot the container
* Remove the container
* Enable the container (the container to be launched at boot)
* Disable the container at startup
* Copy files from host in to a container
* Login the container shell
* Pull and register containers(raw, tar and docker images)
* Bootstrap **Debian** container ("jessie" and newer are supported)
* Bootstrap **Ubuntu** container ("xenial" and newer are supported)
* Bootstrap **Arch Linux** container


Roadmap
########

nspctl is under development. First release will be released soon.