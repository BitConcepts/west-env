<!-- SPDX-License-Identifier: Apache-2.0 -->

# west-env

`west-env` is a workspace-first west extension for reproducible Zephyr build
environments. It lets a standard west workspace run builds either directly on
the host or inside a container, without changing Zephyr itself or replacing the
standard `west build` workflow.

## Why this exists

Zephyr projects often need a reproducible toolchain story without forcing every
developer and CI system to hand-maintain identical host environments.
`west-env` keeps the west workspace as the source of truth and treats
containers as an implementation detail for providing tools and dependencies.

## Features

* Native or container-backed execution
* Docker and Podman engine selection
* Manifest-local configuration via `west-env.yml`
* Standard `west build` argument passthrough
* Workspace-relative behavior that follows normal west expectations
* A copyable reference workspace for onboarding and CI bootstrapping
* Unit tests for config loading, engine selection, path handling, and shell selection

## Quick start

1. Copy `example/workspace/` into a new directory.
2. Run the platform bootstrap script from that copied workspace root.
3. Run `west env doctor`.
4. Run `west env build ...`.

If you are starting fresh, begin with [`example/README.md`](example/README.md).
That copied workspace root is where you run bootstrap, doctor, shell, and build commands.

## Workspace model

`west-env` must be used from inside a valid west workspace.
The repository itself is not a workspace.

This repository is not a workspace and must not contain:

* `.west/`
* `zephyr/`
* `modules/`
* build output
* virtual environments

A copy-only reference workspace lives under `example/workspace/`.
Copy the contents of that directory into a new workspace root and work there;
do not execute the example in place inside this repository.

The intended relationship is:

* this repository defines the extension
* your copied workspace owns `.west/`, `zephyr/`, `modules/`, `.venv/`, and `build/`
* the container image, if used, owns only tools and dependencies

See [`example/README.md`](example/README.md) for the step-by-step setup flow.

## Documentation map

* [`example/README.md`](example/README.md): how to create and use a workspace
* [`container/README.md`](container/README.md): container image contract and host/container responsibilities

## Configuration

`west-env` reads `west-env.yml` from the manifest directory.

Container-backed example:

```yaml
env:
  type: container
  container:
    engine: auto
    image: ghcr.io/bitconcepts/zephyr-build-env:latest
```

Native example:

```yaml
env:
  type: native
```

Supported values:

* `env.type: native`
* `env.type: container`
* `env.container.engine: auto | docker | podman`

When `engine: auto` is used and both engines are present, Docker is preferred
and `west env doctor` reports the selection.

## Commands

`west-env` adds the following subcommands:

```sh
west env init
west env build [--container] [west build args...]
west env shell [--container]
west env doctor
```

### `west env init`

Validates the selected execution environment for the current workspace.

* In native mode this is effectively a no-op.
* In container mode it verifies that the workspace layout is valid and that the
  container can be started.

### `west env build`

Runs `west build` natively or inside a container.
All arguments after `build` are passed through to `west build`.

Examples:

```sh
west env build -b native_sim zephyr/samples/hello_world
west env build --container -b native_sim zephyr/samples/hello_world
```

If `west build` accepts an argument, `west env build` should pass it through.

When switching between native and container execution, remove any existing
build directory before rebuilding so CMake does not reuse stale cache paths.

### `west env shell`

Opens an interactive shell in the selected environment.
Host shells follow the host platform, while container shells use `/bin/sh`.

### `west env doctor`

Checks Python, west, container engine availability, image availability, and
whether the workspace is visible inside the selected container engine.

## Recommended first-run workflow

The recommended starting flow is:

1. Create a new empty directory for a west workspace.
2. Copy `example/workspace/` into that directory.
3. Run the platform bootstrap script.
4. Open the workspace shell.
5. Run `west env doctor`.
6. Build a known-good Zephyr sample.

This keeps the extension repository clean while making the workspace layout
obvious to both developers and CI.

## Host platform notes

Container-backed builds work best on Linux and WSL2-backed Docker setups.
On native Windows with Docker Desktop, mounting workspaces from the Windows
filesystem is expected to be functional but slower than keeping the workspace
inside WSL2.

macOS and Podman are supported by design, but should still be considered
validation targets rather than fully proven environments until exercised in
dedicated end-to-end testing.

## Validation status

Currently covered in the repository:

* unit tests for manifest-local config loading
* unit tests for Docker-only, Podman-only, and auto engine selection
* unit tests for workspace-relative container working-directory behavior
* unit tests for Docker and Podman workspace checks
* unit tests for Windows and POSIX host shell selection

See the test suite under `tests/`.

## Validation roadmap

Additional validation work should focus on real end-to-end runs, not just unit
tests. The next important scenarios are:

* Docker on native Windows with a workspace on the Windows filesystem
* Docker in WSL2 with a workspace in the Linux filesystem
* Docker on native Linux
* Podman on native Linux
* Podman rootless behavior for mounted west workspaces
* macOS with Docker Desktop
* example workspace bootstrap and `west env doctor` from a clean checkout
* at least one sample build in native mode and one in container mode
* switching the same workspace from native to container and back
* CI coverage that exercises at least one Docker job and one native job

## Project status

This project is experimental and intended for design exploration, local
development, CI experimentation, and upstream west/Zephyr discussion.

## License

Apache-2.0
