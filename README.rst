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

Installation
############

Requirements:
*************

- Python >=3.8

Dependencies:
*************

- systemd-container package

For Debian and Ubuntu:

.. code-block::

  $ apt-get install systemd-container

For Centos, Fedora or Redhat Based Distributions:

.. code-block::

  $ yum install systemd-container

or

.. code-block::

 $ dnf install systemd-container

.. note::

  Gentoo with systemd and Arch Linux users don't need to install any packages.

Install:
********

**From Github:**

* Clone this repository:

.. code-block::

    $ git clone https://github.com/mofm/nspctl

* and install via pip:

.. code-block::

    $ pip install nspctl/

If you would like to install for your user:

.. code-block::

    $ pip install --user nspctl/

and you need to add '.local/bin' directory to your path

.. code-block::

    $ export PATH="~/.local/bin/:$PATH"

Usage:
######

**Synopsis:**

.. code-block::

  nspctl [ arguments ] [ options ] [ container name | URL | distribution ] [ ... ]

Commands:
*********

- *list* : List currently running (online) containers.

.. code-block::

  $ nspctl list

- *list-stopped* : List stopped containers.( shortopts: 'lss')

.. code-block::

  $ nspctl list-stopped
  $ nspctl lss

- *list-running* : List currently running containers.(alias: 'list', shortopt: 'lsr')

.. code-block::

  $ nspctl list-running
  $ nspctl lsr

- *list-all* : List all containers.(shortopt: 'lsa')

.. code-block::

  $ nspctl list-all
  $ nspctl lsa

- *info NAME* : Show properties of container.

.. code-block::

  $ nspctl info ubuntu-20.04

- *start NAME* : Start a container as system service.

.. code-block::

  $ nspctl start ubuntu-20.04

- *reboot NAME* : Reboot a container.

.. code-block::

  $ nspctl reboot ubuntu-20.04

- *stop NAME* : Stop a container. Shutdown cleanly.(alias: 'poweroff')

.. code-block::

  $ nspctl stop ubuntu-20.04

- *terminate NAME* : Immediately terminates container without cleanly shutting it down.

.. code-block::

  $ nspctl terminate ubuntu-20.04

- *poweroff NAME* : Poweroff a container. Shutdown cleanly.

.. code-block::

  $ nspctl poweroff ubuntu-20.04

- *enable NAME* : Enable a container as a system service at system boot.

.. code-block::

  $ nspctl enable ubuntu-20.04

- *disable NAME* : Disable a container as a system service at system boot.

.. code-block::

  $ nspctl disable ubuntu-20.04

- *remove NAME* : Remove a container completely.

.. code-block::

  $ nspctl remove ubuntu-20.04

- *shell NAME* : Open an interactive shell session in a container.

.. code-block::

  $ nspctl shell ubuntu-20.04

- *copy-to NAME SOURCE DESTINATION* : Copies files from the host system into a running container.

.. code-block::

    $ nspctl copy-to ubuntu-20.04 /home/hostuser/magicfile /home/containeruser/

Container Operations:
*********************

- *pull-tar URL NAME* : Downloads a .tar container image from the specified URL.(tar, tar.gz, tar.xz, tar.bz2)

.. code-block::

  $ nspctl pul-tar https://github.com/mofm/meta-econ/releases/download/v0.3.0-r2/econ-tiny-nginx-20220123-qemux86-64.tar.xz econ-nginx

- *pull-raw URL NAME* : Downloads a .raw container from the specified URL.(qcow2 or compressed as gz, xz, bz2)

.. code-block::

  $ nspctl pull-raw https://download.fedoraproject.org/pub/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-Base-35-1.2.x86_64.raw.xz fedora-cloud-base-35

- *bootstrap NAME DIST VERSION* : Bootstrap a container from package servers. Supported Distributions are Debian, Ubuntu and Arch Linux.

.. code-block::

  $ nspctl bootstrap ubuntu-20.04 ubuntu focal
  $ nspctl bootstrap debian-bullseye debian stable
  $ nspctl bootstrap arch-test arch


Roadmap
########

nspctl is under development.