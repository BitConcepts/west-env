# west-env

`west-env` is a west extension that provides reproducible build environments for
Zephyr projects. It allows developers to build Zephyr applications using either
their native host environment or a container-backed environment managed by west.

Containers are treated as an implementation detail, enabling consistent
toolchains across developers and CI without modifying Zephyr itself.

## Features

- Native or container-backed builds
- Docker and Podman support
- Config-driven behavior (`west-env.yml`)
- No Zephyr core changes required
- Designed to integrate naturally with west workflows

## Installation

Clone the repository and install in editable mode:

```sh
pip install -e .
```

Bootstrap helper:

```sh
./bootstrap.sh
```

## Configuration

Create a west-env.yml file in your workspace root:

```yaml
env:
  type: container
  container:
    engine: docker
    image: ghcr.io/zephyrproject-rtos/sdk:0.17.0
```

## Usage
```sh
west env init
west env build
west env shell
```

Pass additional arguments directly to west build:

```sh
west env build -b nrf52840dk/nrf52840 samples/hello_world
```

## Design Goals

* Reproducibility over convenience
* Minimal surface area
* Optional and non-intrusive
* Alignment with existing Zephyr and west concepts

## Status

This project is currently experimental and intended for discussion,
prototyping, and upstream evaluation.

## License

Apache-2.0
