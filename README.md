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

The `west-env` repository itself is **not** a workspace and must not be treated
as one:

* no `.west/`
* no `zephyr/`
* no `modules/`
* no build artifacts

To avoid confusion, a **copy-only reference workspace template** is provided
under `example/`.

> ⚠️ The contents of `example/` are **not meant to be executed in place**.
> Always copy the example workspace to a separate directory before using it.

👉 **See [`example/README.md`](example/README.md) for step-by-step workspace setup instructions.**

---

## Example: Building hello_world

Once your workspace is set up (see `example/README.md`) and the environment
checks pass, you can build a Zephyr sample using `west-env`.

### 1. Enter the workspace shell

From the workspace root:

```cmd
scripts\shell.cmd
````

This ensures the correct Python environment and tooling are active.

---

### 2. Verify environment health

```sh
west env doctor
```

All checks should pass before continuing.

---

### 3. Build the hello_world sample

```sh
west env build -b nrf52840dk/nrf52840 samples/hello_world
```

When container mode is enabled in `west-env.yml`, the build will be executed
inside the configured container automatically.

Build artifacts will appear under:

```
build/
```

---

### 4. (Optional) Force container execution

To explicitly force container execution regardless of configuration:

```sh
west env build --container -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
```

This is useful for CI validation or debugging container behavior.

---

## Configuration

Create a `west-env.yml` file in your workspace root:

```yaml
env:
  type: container
  container:
    engine: auto   # docker | podman | auto
    image: ghcr.io/bitconcepts/zephyr-build-env:latest
```

---

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
west env build -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
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
