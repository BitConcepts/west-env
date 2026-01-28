<!-- SPDX-License-Identifier: Apache-2.0 -->

# west-env Container Image Contract

This document defines the **required contract** for container images used by
`west-env`, and explains how those images are used from **Windows** and
**POSIX/Linux** hosts.

Containers are an **implementation detail** used to provide a reproducible,
portable build environment for Zephyr. They are not workspaces and must not
contain project state.

If an image violates this contract, `west-env` behavior is undefined.

---

## Purpose

The container image exists to provide:

* A consistent toolchain
* A complete set of Zephyr build dependencies
* A stable execution environment for CI and developers

The **workspace remains host-owned** and is mounted into the container at runtime.

---

## Responsibilities of the Container Image

### 1. Base system and build tools

The image **must include** all native build tools required by Zephyr, including:

* CMake (compatible with the target Zephyr version)
* Ninja
* GNU build tools (`gcc`, `make`, etc.)
* Device Tree Compiler (`dtc`)
* Common utilities (`git`, `wget`, `file`, etc.)

These are infrastructure dependencies, not workspace concerns.

---

### 2. Zephyr SDK (toolchain)

The image **must include** a compatible Zephyr SDK and expose it via:

```

ZEPHYR_TOOLCHAIN_VARIANT=zephyr
ZEPHYR_SDK_INSTALL_DIR=/opt/zephyr-sdk

```

The SDK version must be:

* Explicitly pinned
* Documented in the image
* Compatible with the Zephyr version used by the workspace

The container is the **sole owner** of the toolchain.

---

### 3. Python (system-wide, no virtual environment)

The container uses **system Python**, not a Python virtual environment.

The image **must include**:

* `python3`
* `pip`
* All Python dependencies required by the supported Zephyr version

The **authoritative source** of Python dependencies is:

```

zephyr/scripts/requirements.txt

```

To ensure correctness and avoid dependency drift, the image should:

1. Temporarily clone the matching Zephyr version during image build
2. Install Python dependencies from `scripts/requirements.txt`
3. Remove the temporary clone

Runtime installation of Python packages is not allowed.

---

### 4. `west`

The image **must have `west` installed** system-wide and available on `PATH`.

The installed version must meet or exceed the minimum version required by the
target Zephyr release.

---

## What the Container Must NOT Do

The container image **must not**:

* Contain a west workspace
* Contain `.west/`, `zephyr/`, or `modules/`
* Permanently clone or pin Zephyr source
* Create or activate a Python virtual environment
* Modify, generate, or assume workspace layout
* Persist build artifacts or mutable state

All workspace state is owned by the host and mounted into the container.

---

## Workspace Mounting Rules

When `west-env` executes commands in a container:

* The **west workspace root** (the directory containing `.west/`) is mounted to:

```

/work

````

* The container working directory is set to the **same relative subdirectory**
  the user was in on the host.

This guarantees:

* `west build` always runs inside a valid workspace
* Nested workspace layouts are supported
* Relative paths behave identically on host and container

---

## Host vs Container Responsibilities

| Concern              | Host                              | Container                         |
|----------------------|-----------------------------------|-----------------------------------|
| Workspace state      | Owns `.west/`, `zephyr/`, modules | Never owns state                  |
| Python environment   | `.venv` (user tools, west-env)    | System Python (build deps)        |
| Zephyr source        | Managed via `west.yml`            | Mounted at runtime                |
| Toolchain & SDK      | Not required                      | Fully provided                    |
| Reproducibility      | Config-driven                     | Image-defined                     |

This separation is intentional and required.

---

## Using the Container on Windows

### Requirements

* Docker Desktop (WSL2 backend recommended)
* `west-env` installed in the workspace `.venv`
* No requirement for Python, CMake, or SDK on the host

### Key Rules (Windows)

* **Never pass Windows paths** (`C:\...`) as Docker working directories
* All paths are mounted by `west-env`
* The container always works in `/work`

### Typical Flow

From the workspace root:

```cmd
scripts\bootstrap.cmd
scripts\shell.cmd
west env doctor
west env build -b nrf52840dk/nrf52840 samples\hello_world
````

Notes:

* The build runs inside the container automatically
* No manual `docker run` is required
* No container shell is required
* Build output appears in the host workspace

---

## Using the Container on POSIX / Linux / macOS

### Requirements

* Docker or Podman
* `west-env` installed in the workspace `.venv`

### Typical Flow

From the workspace root:

```sh
./scripts/bootstrap.sh   # if provided
source .venv/bin/activate
west env doctor
west env build -b nrf52840dk/nrf52840 samples/hello_world
```

Notes:

* Path translation is trivial on POSIX systems
* Container execution is transparent
* Relative paths behave identically to native builds

---

## Container Engine Selection

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
* Engine detection failures are reported clearly
* Missing images produce warnings, not crashes

---

## Design Rationale

This contract enforces:

* Reproducible builds across developers and CI
* Clear ownership of mutable state
* Zero coupling between container images and workspace layout
* Alignment with Zephyr and west mental models
* Identical workflows on Windows and POSIX hosts

The container provides **tools and dependencies only**.
The workspace provides **source and state only**.

---

## Summary

If you remember only one rule:

> **The container provides the environment.
> The workspace provides the project.**

Anything else is a bug.
