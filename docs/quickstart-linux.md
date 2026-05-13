# Linux Quick-Start — west-env

## Prerequisites

```sh
# Podman (preferred)
sudo apt install podman          # Debian/Ubuntu
sudo dnf install podman          # Fedora/RHEL

# Or Docker
curl -fsSL https://get.docker.com | sh

# Python 3.10+ and west
pip install west
```

---

## 1. Install west-env

```sh
pip install -e path/to/west-env
```

Or reference it from your west manifest using `west-commands:`.

---

## 2. Configure west-env.yml

In your manifest directory (sibling of `west.yml`):

```yaml
env:
  backend: auto            # selects podman-native or docker-native
  workspace_mode: bind     # bind mount is fine on Linux
  image: ghcr.io/your-org/zephyr-build-env:latest

cache:
  ccache: true
  modules: true

git:
  credential_helper: auto  # uses SSH_AUTH_SOCK if set

jlink:
  mode: host               # flash with Linux J-Link tools
```

---

## 3. Verify and build

```sh
west env doctor              # check backend, credentials, J-Link
west env build -b nrf52840dk app/
west env flash build/zephyr/zephyr.hex
```

On Linux with bind mount, `west env sync` is optional — the workspace is
mounted directly into the container.

---

## 4. Generate VSCode tasks

```sh
west env generate-tasks
```

Creates `.vscode/tasks.json` with `.sh` wrapper tasks. Open the workspace in
VS Code and use **Terminal > Run Task** to access `west-env: build` etc.

---

## Common commands

```sh
west env doctor           # verify setup
west env build -b <board> <app>
west env shell            # interactive container shell
west env cache stats      # volume sizes + ccache hit rate
west env cache reset      # clear all caches
```
