# west-env

`west-env` is a west extension that provides reproducible build environments for
Zephyr projects. It allows developers to build Zephyr applications using either
their native host environment or a container-backed environment managed by west.

Containers are treated as an implementation detail, enabling consistent
toolchains across developers and CI without modifying Zephyr itself.

---

## Features

* Native or container-backed builds
* Docker and Podman support
* Config-driven behavior (`west-env.yml`)
* No Zephyr core changes required
* Designed to integrate naturally with west workflows

---

## Workspace Setup (Required)

`west-env` is a **west extension**, not a standalone tool.  
It must be used from within a **west workspace**.

The `west-env` repository itself is **not** a workspace and does not act as one.

To avoid confusion, reference workspace bootstrap scripts are provided under
`example/`. These scripts demonstrate the recommended way to create a clean
workspace and integrate `west-env`.

👉 **See [`example/README.md`](example/README.md) for step-by-step workspace setup instructions.**

---

## Configuration

Create a `west-env.yml` file in your workspace root:

```yaml
env:
  type: container
  container:
    engine: auto   # docker | podman | auto
    image: ghcr.io/zephyrproject-rtos/sdk:0.17.0
````

### Container engine selection

The container engine may be selected explicitly or auto-detected.

Supported values:

* `docker`: force Docker
* `podman`: force Podman
* `auto`: automatically select an available engine (default)

When `engine: auto` is used and both Docker and Podman are available,
Docker is selected by default and `west env doctor` will emit a warning.
Set the engine explicitly to avoid ambiguity.

---

## Usage

```sh
west env init
west env build
west env shell
west env doctor
```

Pass additional arguments directly to `west build`:

```sh
west env build -b nrf52840dk/nrf52840 samples/hello_world
```

---

## Design Goals

* Reproducibility over convenience
* Minimal surface area
* Optional and non-intrusive
* Alignment with existing Zephyr and west concepts

---

## Status

This project is currently experimental and intended for discussion,
prototyping, and upstream evaluation.

---

## License

Apache-2.0
