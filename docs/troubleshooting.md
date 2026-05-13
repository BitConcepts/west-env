# Troubleshooting — west-env

## `west env doctor` says no backend found

**Symptom:** `[FAIL] No supported container backend found on win32.`

**Fixes:**
1. Install Podman for Windows and run `podman machine init && podman machine start`.
2. Or install Docker Desktop and ensure the Docker engine is running.
3. Run `west env doctor` again — it will show what was probed and why it was skipped.

---

## Windows: performance warning about Docker Desktop bind mounts

**Symptom:** `[WARN] Docker Desktop (WSL2 bind mount) detected. Build performance on C:\ paths may be poor.`

**Fix:** Install Podman for Windows and enable Hyper-V:
```powershell
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All
winget install RedHat.Podman
podman machine init --now
```

Then run `west env doctor` — it should select `podman-machine-hyperv`.

---

## `west env sync` fails with "no such container engine"

**Symptom:** `docker: command not found` or `podman: command not found`

**Fix:** Ensure the container engine binary is on `PATH`. Verify with `west env doctor`.

---

## Windows: Podman machine not running

**Symptom:** `[SKIP] podman-machine-hyperv: No running Podman machine — run: podman machine start`

**Fix:**
```powershell
podman machine start
west env doctor   # should now show [PASS] backend selected: podman-machine-hyperv
```

---

## Git operations inside container fail (permission denied / authentication)

**Symptom:** `git clone` inside the container fails with `Permission denied (publickey)`.

**Fix:** Ensure SSH agent is running and your key is loaded:
```powershell
# Windows
Start-Service ssh-agent
ssh-add ~/.ssh/id_ed25519

west env doctor   # should show [PASS] git credentials: openssh-agent
```

On Linux/macOS:
```sh
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

If SSH is not an option, configure HTTPS with a credential manager:
```sh
git config --global credential.helper manager  # GCM
```

See [git-credentials.md](git-credentials.md) for more.

---

## J-Link not found

**Symptom:** `[WARN] J-Link host tools not found in PATH or standard locations`

**Fix:** Install SEGGER J-Link from https://www.segger.com/downloads/jlink/
and ensure `JLinkExe` (Linux/macOS) or `JLink.exe` (Windows) is on `PATH`.

Default search paths:
- **Windows:** `C:\Program Files\SEGGER\JLink\`
- **Linux:** `/opt/SEGGER/JLink/`
- **macOS:** `/Applications/SEGGER/JLink/`

---

## `.vscode/tasks.json` tasks fail with "command not found"

**Symptom:** VSCode task `west-env: build` errors with `west-env-build.ps1: command not found`.

**Fix:** Run `west env generate-tasks` first to generate the wrapper scripts, then reload VSCode.

---

## Sync excludes a file I need

**Symptom:** A source file is not appearing in the container workspace.

**Fix:** Check and override the exclusion list in `west-env.yml`:
```yaml
sync:
  exclude:
    - build
    - .cache
    # remove or add patterns as needed
```

---

## Build artifacts not appearing after `west env sync --back`

**Symptom:** `.elf`/`.hex` files are not copied back.

**Cause:** `sync --back` only copies files with extensions: `.elf`, `.bin`, `.hex`, `.map`, `.lst`, `.s19`.

**Fix:** Confirm your build produced output files inside `/work/build/` in the container. Run `west env shell` and check `ls /work/build/zephyr/`.

---

## macOS: slow builds with `workspace_mode: bind`

**Symptom:** Builds are much slower than expected on macOS.

**Fix:** Switch to `workspace_mode: sync` which uses a named volume inside the Podman/Docker machine, avoiding VirtioFS overhead:
```yaml
env:
  workspace_mode: sync
```

Then run `west env sync` before each build.

---

## Container image not found

**Symptom:** `docker: Error response from daemon: manifest unknown`

**Fix:** Ensure the image name and tag in `west-env.yml` are correct and that you are authenticated to the registry:
```sh
docker login ghcr.io
```
or
```sh
podman login ghcr.io
```
