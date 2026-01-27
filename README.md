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
A separate workspace directory is required.

### Windows (recommended workflow)

#### 1. Create a workspace directory

```cmd
mkdir west-env-ws
cd west-env-ws
````

This directory will become your west workspace.

#### 2. Run bootstrap

```cmd
bootstrap.cmd
```

This will:

* create a Python virtual environment (`.venv`)
* install `west`
* create a minimal `west.yml`
* fetch `west-env` into `modules/west-env`
* initialize the west workspace

> ⚠️ `bootstrap.cmd` must **not** be run inside the `west-env` repository.
> It will fail intentionally if run from there.

#### 3. Enter the workspace shell

```cmd
shell.cmd
```

You should see output similar to:

```
Python: vX.Y.Z
West: vA.B.C
```

You are now in the workspace root with the correct environment activated.

#### 4. Verify installation

```cmd
west env doctor
```

If this succeeds, the workspace is correctly set up.

### Resulting layout

```
west-env-ws/
├─ .venv/
├─ .west/
├─ west.yml
├─ bootstrap.cmd
├─ shell.cmd
└─ modules/
   └─ west-env/
```

This mirrors how west extensions are used in real Zephyr workspaces and CI.

---

## Configuration

Create a `west-env.yml` file in your workspace root:

```yaml
env:
  type: container
  container:
    engine: auto   # docker | podman | auto
    image: ghcr.io/zephyrproject-rtos/sdk:0.17.0
```

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
