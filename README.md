# west-env

`west-env` is a **west extension** that provides **reproducible build environments**
for Zephyr projects.

It enables developers to build Zephyr applications using either:

* a **native host environment**, or
* a **container-backed environment** (Docker / Podman)

—without modifying Zephyr itself or changing existing west workflows.

Containers are treated strictly as an **implementation detail**: they provide a
known-good toolchain and dependency set, while the west workspace, source code,
and build artifacts remain fully host-owned and west-native.

This repository is intended to support **community discussion**, **show-and-tell
demonstrations**, and eventual **RFC-style design exploration** within the
Zephyr Project (e.g. via the *Ideas* discussion category).

---

## Features

* Native or container-backed builds
* Docker and Podman support (engine selectable)
* Config-driven behavior (`west-env.yml`)
* No Zephyr core changes required
* Clean integration with standard west commands
* Works across Windows, WSL2, Linux, macOS, and CI (see status below)

---

## What `west-env` Is (and Is Not)

### What it **is**

* A **west extension**
* A reproducible build environment mechanism
* A thin orchestration layer over `west build`
* A way to standardize toolchains without forking Zephyr
* An experiment aligned with west and Zephyr mental models

### What it is **not**

* A west workspace
* A replacement for west
* A Zephyr fork
* A container abstraction users interact with directly
* A build system of its own

---

## Workspace Model (Required)

`west-env` must be used **from within a west workspace**.

The `west-env` repository itself is **not** a workspace and must never contain:

* `.west/`
* `zephyr/`
* `modules/`
* build output
* virtual environments

To demonstrate the correct layout and usage, a **copy-only reference workspace**
is provided under `example/`.

> ⚠️ Nothing under `example/` is meant to be executed in place.  
> Always copy the example workspace to a new directory and work from there.

👉 **See [`example/README.md`](example/README.md) for authoritative, step-by-step
workspace setup and build demonstration instructions.**

---

## Host Platforms and Performance

### Windows (native)

`west-env` works on native Windows. However, when using container-backed builds
with Docker Desktop and a workspace located on the Windows filesystem
(e.g. `C:\Users\...`), build performance will be **significantly slower**.

This is a known limitation of bind-mounting NTFS paths into Linux containers.

### WSL2 (recommended on Windows)

For best performance on Windows:

> **Use WSL2 and keep the workspace inside the WSL2 filesystem**
> (e.g. `/home/user/...`, not `C:\...`).

Benefits include:

* Near-native Linux filesystem performance
* Dramatically faster CMake and Ninja builds
* Behavior identical to Linux and CI
* Avoidance of Docker Desktop filesystem translation overhead

### Linux (native)

On native Linux systems, `west-env` runs as expected and performs optimally with
container-backed builds.

### macOS

macOS is expected to work similarly to Linux when using Docker Desktop, but has
not yet been explicitly validated (see status below).

---

## Container Integration (High-Level)

When container mode is enabled:

* `west-env` transparently runs `west build` **inside a container**
* the west workspace (topdir) is mounted into the container
* the container provides:
  * toolchain
  * SDK
  * build dependencies
* all source code, workspace state, and build artifacts remain on the host

The container image is treated as a **build artifact** that is pulled from a
registry as needed, not something users interact with directly.

**See [`container/README.md`](container/README.md) for the container contract,
image expectations, and design constraints.**

---

## Configuration (`west-env.yml`)

Behavior is controlled via a `west-env.yml` file located alongside the manifest.

Example (container-backed builds):

```yaml
env:
  type: container
  container:
    engine: auto      # docker | podman | auto
    image: ghcr.io/bitconcepts/zephyr-build-env:latest
````

Supported modes:

* `type: native`
  Run builds directly on the host.

* `type: container`
  Run builds inside the configured container.

When `engine: auto` is selected and multiple engines are available, Docker is
preferred and `west env doctor` will emit a warning.

---

Here’s the **updated section you can drop straight into the main `README.md`**, expanding **west env usage fully**, including flags like `--container`, **without changing the overall structure or intent** of the document you already have.

I’m giving you **only the parts that need to be added/replaced**, not a whole rewrite, so it’s easy to apply.

---

## Commands and Usage

`west-env` adds a set of subcommands under `west env` that integrate directly
with standard west workflows.

```sh
west env init
west env build [options] [west build args...]
west env shell
west env doctor
````

All commands must be run from within a valid west workspace.

---

### `west env init`

```sh
west env init
```

Initializes the environment for the current workspace.

Behavior depends on configuration:

* In native mode, this is effectively a no-op
* In container mode, this verifies container availability and workspace layout

This command does **not** create a workspace and does not modify repository
state. It assumes the workspace already exists and is valid.

---

### `west env build`

```sh
west env build [--container] [west build arguments...]
```

Runs `west build`, either natively or inside a container.

All arguments not recognized by `west env` are passed directly to
`west build`.

#### Common options

* `--container`
  Force container execution regardless of `west-env.yml` configuration.

#### Example (container-backed build)

```sh
west env build --container -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
```

#### Example (native build)

```sh
west env build -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
```

Build output is written to the standard `build/` directory.

### Switching between container and native builds

When switching a workspace between **container-backed** and **native** builds,
the existing build directory should be removed before rebuilding.

Container and native builds may differ in:

* absolute paths
* toolchain locations
* SDK layout
* CMake cache contents

Reusing a build directory created in one mode while building in the other can
lead to confusing configuration errors or stale paths.

Before switching modes, remove the build directory:

```sh
rm -rf build/
````

Then rerun the build using the desired mode.

This behavior is consistent with standard `west build` and CMake expectations
and is not specific to `west-env`.

---

### `west env shell`

```sh
west env shell [--container]
```

Opens an interactive shell:

* in the host environment (default), or
* inside the configured container when `--container` is specified or container
  mode is enabled in `west-env.yml`.

This is useful for debugging toolchains, inspecting the environment, or running
manual build commands.

---

### `west env doctor`

```sh
west env doctor
```

Performs a series of environment checks, including:

* Python availability
* west installation
* container engine detection
* container image availability
* workspace visibility inside the container (when applicable)

This command is intended to fail early and clearly when configuration or
environment issues are detected.

---

### Argument passthrough behavior (important)

`west env build` intentionally forwards **all unknown arguments** to
`west build`.

This includes, but is not limited to:

* `-b <board>`
* `-p`, `--pristine`
* build directory arguments
* source directory arguments

If an argument accepted by `west build` is rejected by `west env build`,
this is considered a bug.

---

### Summary of flags

| Flag          | Applies to   | Description                            |
| ------------- | ------------ | -------------------------------------- |
| `--container` | build, shell | Force execution inside a container     |
| *(none)*      | all          | Use behavior defined in `west-env.yml` |


For a complete, end-to-end walkthrough (including bootstrapping and shells),
refer to the example workspace documentation.

**See [`example/README.md`](example/README.md)**

---

## Design Goals

* Reproducibility over convenience
* Explicit, debuggable behavior
* Minimal surface area
* No mutation of repository state
* Clear separation of responsibilities:

  * the workspace owns source and state
  * the container owns tools and dependencies
* Strong alignment with west and Zephyr concepts

---

## Project Status

This project is currently **experimental** and intended for:

* prototyping
* design discussion
* show-and-tell demonstrations
* CI experimentation
* potential upstream RFC exploration

APIs, behavior, and structure may evolve based on feedback from the
Zephyr community.

### Tested Environments

Validated:

* Docker Desktop on **Windows 11**
* Docker running inside **WSL2**

Not yet validated:

* Native Linux (outside WSL2)
* macOS
* Podman (rootless or rootful)

Podman support is **designed in** and expected to work, but has not been explicitly
tested at this time.

---

## License

Apache-2.0
