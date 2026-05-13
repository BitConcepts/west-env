# macOS Quick-Start — west-env

## Prerequisites

```sh
# Podman (preferred)
brew install podman
podman machine init
podman machine start

# Or Docker Desktop from docker.com

# Python 3.10+ and west
pip3 install west
```

---

## 1. Install west-env

```sh
pip install -e path/to/west-env
```

---

## 2. Configure west-env.yml

```yaml
env:
  backend: auto            # selects podman-machine or docker-machine
  workspace_mode: sync     # named volume avoids macOS VirtioFS overhead
  image: ghcr.io/your-org/zephyr-build-env:latest

cache:
  ccache: true
  modules: true

git:
  credential_helper: auto  # uses SSH_AUTH_SOCK

jlink:
  mode: host               # flash with macOS J-Link tools
```

> **Performance note:** macOS VirtioFS bind mounts can be slow for large Zephyr
> trees. Using `workspace_mode: sync` (named volume) is recommended.

---

## 3. Verify and build

```sh
west env doctor
west env sync
west env build -b nrf52840dk app/
west env sync --back
west env flash build/zephyr/zephyr.hex
```

---

## 4. Generate VSCode tasks

```sh
west env generate-tasks
```

Creates `.vscode/tasks.json` with `.sh` wrapper tasks.

---

## Common commands

```sh
west env doctor           # verify setup
west env sync             # source → Podman machine volume
west env build -b <board> <app>
west env sync --back      # artifacts → macOS
west env cache stats
```
