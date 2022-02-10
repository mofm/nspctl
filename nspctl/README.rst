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

Currently implemented features are:

* containers list
    - running containers
    - stopped containers
    - all containers
* containers info
* containers status
* start the container
* stop the container
* reboot the container
* remove the container
* enable the container (the container to be launched at boot)
* disable the container at startup
* copy files from host in to a container
* login the container shell
* pull and register containers(raw, tar and docker images)


Roadmap
########

nspctl is under development. First release will be released soon.