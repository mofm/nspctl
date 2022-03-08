# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- added clean. clean all hidden vm and container images
- added clean-all. clean all installed vm and container images
- added exec. runs a new command in a running container

### Changed

- version number changed to dev1
- removed pull-dkr feature. no longer supported by machinectl

### Fixed

nothing

## [0.0.1-dev01] 04/03/2022

### Added
nspctl first release

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
* Bootstrap Debian container ("jessie" and newer are supported)
* Bootstrap Ubuntu container ("xenial" and newer are supported)
* Bootstrap Arch Linux container


[Unreleased]: https://github.com/mofm/nspctl/compare/0.0.1-dev01...HEAD
[0.0.1-dev01]: https://github.com/mofm/meta-econ/releases/tag/0.0.1-dev01
