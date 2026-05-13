<!-- SPDX-License-Identifier: Apache-2.0 -->

# west-env

`west-env` is a cross-platform Zephyr RTOS developer environment manager. It
provides a unified `west env` CLI that adapts to your host OS and available
container or VM backend, delivering reproducible builds on **Windows, Linux,
and macOS** without changing Zephyr itself or the standard `west build` workflow.

**Windows works natively.** You edit files in Windows VSCode, flash with
Windows J-Link tools, and use PowerShell — no WSL editing, no Remote WSL
extension, no slow C:\\ bind-mount builds.

## Why this exists

Zephyr projects often need a reproducible toolchain story without forcing every
developer and CI system to hand-maintain identical host environments.
`west-env` keeps the west workspace as the source of truth and treats
containers as an implementation detail for providing tools and dependencies.

## Platform support

| Platform | Recommended backend | Workspace | Flash |
|----------|--------------------|-----------|-----------|
| **Windows** | Podman machine (Hyper-V) | ext4 volume in VM | Windows J-Link |
| **Linux** | Podman or Docker native | Bind mount or volume | Linux J-Link |
| **macOS** | Podman machine | Named volume | macOS J-Link |

> **Windows default avoids C:\\ bind mounts.** Source is rsynced into a Linux
> ext4 volume inside a Podman Hyper-V VM. Build times are comparable to native
> Linux — not WSL2 bind-mount slow.

## Features

* **6-backend auto-detection** — Podman Hyper-V, Docker Desktop, Podman native, Docker native, Podman machine (macOS), Docker machine (macOS)
* **4 workspace modes** — `sync` (recommended on Windows), `copy`, `tmpfs`, `bind`
* **Persistent caches** — ccache, west modules, Zephyr SDK, pip (named volumes)
* **Git credential forwarding** — Windows OpenSSH agent socket or HTTPS credential-manager
* **J-Link host flash** — Windows-native J-Link tools on synced artifacts; no USB passthrough needed
* **VSCode integration** — generated `tasks.json` with `.ps1`/`.sh` wrappers; no Remote WSL
* **Workspace sync** — source in, build artifacts out; excluded dirs are never uploaded
* **Manifest-local config** — `west-env.yml` in the manifest directory
* **Full backward compatibility** — existing `env.type: container` config still works

## Quick start

**Platform-specific guides:**
* [Windows quick-start](docs/quickstart-windows.md)
* [Linux quick-start](docs/quickstart-linux.md)
* [macOS quick-start](docs/quickstart-macos.md)

**Minimal flow (any platform):**
```sh
west env doctor          # check backend, credentials, J-Link
west env sync            # push source to container/VM workspace
west env build -b <board> <app>
west env sync --back     # pull .elf/.hex back to host
west env flash build/zephyr/zephyr.hex
```

## Configuration

`west-env` reads `west-env.yml` from the manifest directory (sibling of `west.yml`).

**New format (recommended):**
```yaml
env:
  backend: auto           # auto | podman-machine-hyperv | docker-desktop | podman-native | ...
  workspace_mode: sync    # sync | copy | tmpfs | bind
  image: ghcr.io/bitconcepts/zephyr-build-env:latest

cache:
  ccache: true
  modules: true

git:
  credential_helper: auto  # auto | openssh-agent | credential-manager | none

jlink:
  mode: host              # host | tcp-server | none
```

**Legacy format (still supported):**
```yaml
env:
  type: container
  container:
    engine: auto           # auto | docker | podman
    image: ghcr.io/bitconcepts/zephyr-build-env:latest
```

## Commands

```sh
west env doctor                    # check backend, credentials, J-Link
west env init                      # initialise environment
west env sync                      # source → container/VM
west env sync --back               # artifacts ← host
west env build [-b <board>] [...]   # build in container
west env shell                     # interactive shell
west env flash <artifact.hex>      # flash with host J-Link
west env debug <device>            # start J-Link GDB server
west env cache stats               # show cache volume sizes
west env cache reset [--ccache]    # prune cache volumes
west env benchmark                 # timed build + JSON record
west env generate-tasks            # write .vscode/tasks.json + wrappers
```

## Workspace model

`west-env` must be used from inside a valid west workspace.
The repository itself is not a workspace.

* This repository defines the extension.
* Your workspace owns `.west/`, `zephyr/`, `modules/`, `.venv/`, and `build/`.
* The container image owns only tools and dependencies.

See [`example/README.md`](example/README.md) for the step-by-step setup flow.

## Documentation

* [Windows quick-start](docs/quickstart-windows.md)
* [Linux quick-start](docs/quickstart-linux.md)
* [macOS quick-start](docs/quickstart-macos.md)
* [Git credentials](docs/git-credentials.md)
* [J-Link flashing](docs/flashing.md)
* [Troubleshooting](docs/troubleshooting.md)
* [Architecture](docs/ARCHITECTURE.md)
* [Requirements](docs/REQUIREMENTS.md)
* [Feature plan](docs/FEATURE-PLAN.md)

## Test coverage

122 unit tests across: config, backend detection, workspace sync, cache,
credentials, VSCode generation, platform wrappers, flash, container execution.
Docker integration and native-sim end-to-end tests run in CI on ubuntu-latest.
Unit tests run on Windows, Linux, and macOS × Python 3.10/3.11/3.12.

## Project status

Experimental — designed for local development, CI, and upstream Zephyr discussion.
Slices 2–11 implemented; Slice 12 (docs/troubleshooting) in progress.

## License

Apache-2.0
