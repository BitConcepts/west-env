<!-- SPDX-License-Identifier: Apache-2.0 -->

# west-env Container Image Contract

This document defines the required contract for container images used by
`west-env` and explains how those images relate to the west workspace on the
host.

Containers are an implementation detail used to provide a reproducible,
portable build environment for Zephyr. They are not workspaces and must not
contain project state.

If an image violates this contract, `west-env` behavior is undefined.

## One rule to remember

The container provides the environment.
The workspace provides the project.

## Purpose

The container image exists to provide:

* a consistent toolchain
* a complete set of Zephyr build dependencies
* a stable execution environment for CI and developers

The workspace remains host-owned and is mounted into the container at runtime.

## Responsibilities of the container image

### 1. Base system and build tools

The image must include the native build tools required by Zephyr, including:

* CMake
* Ninja
* GNU build tools such as `gcc` and `make`
* Device Tree Compiler (`dtc`)
* common utilities such as `git`, `wget`, and `file`

These are infrastructure dependencies, not workspace concerns.

### 2. Zephyr SDK or equivalent toolchain

The image must include a compatible Zephyr SDK and expose it via:

```sh
ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk
```

The SDK version must be:

* explicitly pinned
* documented in the image
* compatible with the Zephyr version used by the workspace

The container is the sole owner of the toolchain.

### 3. Python

The container uses system Python, not a Python virtual environment.

The image must include:

* `python3`
* `pip`
* all Python dependencies required by the supported Zephyr version

The authoritative source of Python dependencies is:

```text
zephyr/scripts/requirements.txt
```

To avoid dependency drift, the image should:

1. temporarily clone the matching Zephyr version during image build
2. install Python dependencies from `scripts/requirements.txt`
3. remove the temporary clone

Runtime installation of Python packages is not allowed.

### 4. `west`

The image must have `west` installed system-wide and available on `PATH`.
The installed version must meet or exceed the minimum version required by the
target Zephyr release.

## What the container must not do

The container image must not:

* contain a west workspace
* contain `.west/`, `zephyr/`, or `modules/`
* permanently clone or pin Zephyr source
* create or activate a Python virtual environment
* modify, generate, or assume workspace layout
* persist build artifacts or mutable state

All workspace state is owned by the host and mounted into the container.

## Workspace mounting rules

When `west-env` executes commands in a container:

* the west workspace root, meaning the directory containing `.west/`, is mounted at `/work`
* the container working directory is set to the same relative subdirectory the user was in on the host

This guarantees:

* `west build` always runs inside a valid workspace
* nested workspace layouts are supported
* relative paths behave identically on host and container

## Host responsibilities

The host owns:

* `.west/`
* `west.yml`
* `west-env.yml`
* `.venv/`
* `zephyr/`
* `modules/`
* source changes
* build output

## Container responsibilities

The container owns:

* system Python for build dependencies
* `west`
* the Zephyr SDK or other required toolchains
* CMake, Ninja, `dtc`, Git, and other build tools

This separation is intentional and required.

## Using the container on Windows

### Requirements

* Docker Desktop, preferably with a WSL2 backend
* `west-env` installed in the workspace `.venv`
* no requirement for Python, CMake, or SDK on the host when using container mode

### Key rules

* do not pass Windows paths as container working directories manually
* let `west-env` handle mounting and working-directory selection
* expect native Windows filesystem mounts to be slower than WSL2 filesystem mounts

### Typical flow

From the workspace root:

```cmd
scripts\\bootstrap.cmd
scripts\\shell.cmd
west env doctor
west env build -b native_sim zephyr\\samples\\hello_world
```

## Using the container on POSIX / Linux / macOS

### Requirements

* Docker or Podman
* `west-env` installed in the workspace `.venv`

### Typical flow

From the workspace root:

```sh
./scripts/bootstrap.sh
source .venv/bin/activate
west env doctor
west env build -b native_sim zephyr/samples/hello_world
```

On POSIX hosts, path translation is usually straightforward and container
execution should closely mirror native workspace-relative behavior.

## Container engine selection

The container engine is selected via `west-env.yml`:

```yaml
env:
  type: container
  container:
    engine: auto
    image: ghcr.io/bitconcepts/zephyr-build-env:latest
```

Behavior:

* `auto` selects Docker or Podman if available
* Docker is preferred when both are available
* engine detection failures are reported clearly
* missing images produce warnings instead of fatal errors during doctor checks

## Validation focus areas

The most important runtime validation scenarios for container-backed execution
are:

* Docker on Windows with a workspace on the Windows filesystem
* Docker in WSL2 with a workspace in the Linux filesystem
* Docker on native Linux
* Podman on native Linux
* Podman rootless workspace mounting behavior
* at least one clean bootstrap + doctor + build flow per environment

## Design rationale

This contract enforces:

* reproducible builds across developers and CI
* clear ownership of mutable state
* zero coupling between container images and workspace layout
* alignment with Zephyr and west mental models
* identical workflows on Windows and POSIX hosts

The container provides tools and dependencies only.
The workspace provides source and state only.
