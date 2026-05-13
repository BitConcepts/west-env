# Windows Quick-Start — west-env

## Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10–3.12 | [python.org](https://www.python.org/downloads/) |
| west | `pip install west` |
| Podman for Windows | [podman.io](https://podman.io) (preferred) or Docker Desktop |
| SEGGER J-Link | [segger.com/downloads/jlink](https://www.segger.com/downloads/jlink/) (for flashing) |
| Windows OpenSSH | Already included in Windows 10/11 |

**PowerShell 7 (pwsh)** is required. Install from the Microsoft Store or GitHub releases.

---

## 1. Install west-env

In your west workspace root:

```powershell
pip install -e path/to/west-env
```

Or reference it from your west manifest using `west-commands:`.

---

## 2. Verify backend

Run `west env doctor` from your workspace root. Expected output on a machine with Podman Hyper-V:

```
[PASS] Python 3.11.x
[PASS] west is installed

[PASS] backend selected: podman-machine-hyperv
       version: podman version 5.x.x

[PASS] git credentials: openssh-agent
       socket: \\pipe\openssh-ssh-agent

[WARN] J-Link host tools not found in PATH or standard locations
       Install from https://www.segger.com/downloads/jlink/
```

If Hyper-V is unavailable, `doctor` selects `docker-desktop` and warns about bind-mount performance. See [troubleshooting](troubleshooting.md).

---

## 3. Configure west-env.yml

In your manifest directory (sibling of `west.yml`), create `west-env.yml`:

```yaml
env:
  backend: auto            # selects Podman Hyper-V automatically on Windows
  workspace_mode: sync     # recommended on Windows
  image: ghcr.io/your-org/zephyr-build-env:latest

cache:
  ccache: true
  modules: true

git:
  credential_helper: auto  # uses Windows OpenSSH agent if running

jlink:
  mode: host               # flash with Windows J-Link tools
```

---

## 4. Sync and build

```powershell
# Push source files into the VM workspace (excludes build/, .cache/, etc.)
west env sync

# Build inside the container/VM
west env build -b nrf52840dk app/

# Pull build artifacts back to Windows
west env sync --back

# Flash with Windows J-Link
west env flash artifacts/build/zephyr/zephyr.hex
```

---

## 5. Generate VSCode tasks

```powershell
west env generate-tasks
```

This creates:
- `scripts/west-env-build.ps1` (and other action wrappers)
- `.vscode/tasks.json` — tasks that call the PowerShell wrappers

Open the workspace in Windows VSCode. Use **Terminal > Run Task** to see `west-env: build`, `west-env: sync`, etc. **No Remote WSL extension is required.**

---

## Windows-specific notes

- **Edit files in Windows** (`C:\your-workspace\`) — the sync layer copies them to the VM.
- **Do not edit files inside WSL or the container** — those paths are not your source.
- **PowerShell wrappers** (`.ps1`) never call `bash`, `wsl.exe`, or any Linux shell.
- **Git credentials** from Windows are forwarded automatically via the OpenSSH agent socket. You do not need to copy SSH keys into the container.
- **J-Link** runs on Windows and flashes from the synced artifact path. No USB passthrough into the container.
- If you see bind-mount performance warnings, check that Podman Hyper-V is running: `podman machine start`.

---

## Common commands

```powershell
west env doctor                   # check everything
west env sync                     # source → VM
west env build -b native_sim .    # build in container
west env sync --back              # artifacts → Windows
west env flash zephyr.hex         # flash with Windows J-Link
west env cache stats              # show volume sizes
west env cache reset --ccache     # clear compiler cache
west env benchmark                # timed build record
```
