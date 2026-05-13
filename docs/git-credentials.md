# Git Credentials — west-env

`west-env` forwards host Git credentials into the build container so `west update`
and `git clone` of private modules work without copying tokens or keys into images.

## Strategy selection

Configure in `west-env.yml`:

```yaml
git:
  credential_helper: auto  # auto-detect (recommended)
  # or: openssh-agent | credential-manager | none
```

`auto` tries strategies in this order:
1. **openssh-agent** — if `SSH_AUTH_SOCK` is set and the socket exists.
2. **credential-manager** — if `git config --global credential.helper` returns a value.
3. **none** — private repos will fail to clone inside the container.

`west env doctor` reports the active strategy.

---

## Windows: OpenSSH agent

The Windows OpenSSH agent service is the recommended approach for SSH-based remotes.

```powershell
# Enable and start the service (once)
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent

# Add your key
ssh-add $env:USERPROFILE\.ssh\id_ed25519

# Verify
ssh-add -l
```

`west env doctor` will then report `[PASS] git credentials: openssh-agent`.

The agent socket is forwarded into the container automatically. No private key
is ever copied into the container image.

### Note on named-pipe forwarding

The Windows OpenSSH agent uses a named pipe (`\\.\pipe\openssh-ssh-agent`).
Direct forwarding into Linux containers requires a relay tool such as
[npiperelay](https://github.com/jstarks/npiperelay) combined with `SSH_AUTH_SOCK`
pointing to a socat relay socket. `west-env` forwards whatever `SSH_AUTH_SOCK`
is set to; set up the relay first if needed.

---

## Linux / macOS: SSH agent

```sh
# Start agent and add key
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Or use a persistent agent (e.g. keychain, 1Password SSH agent)
```

`SSH_AUTH_SOCK` is forwarded as a read-only bind mount into the container.

---

## HTTPS: Git Credential Manager

For HTTPS remotes (e.g. GitHub PAT, Azure DevOps):

```sh
# Install Git Credential Manager
# https://github.com/git-ecosystem/git-credential-manager

git config --global credential.helper manager
```

`west-env` detects this automatically. The credential manager runs on the
host; the container delegates to it via the Git credential protocol.

**Token security:** No token or credential file is ever copied into the
container image or mounted as a volume. The credential manager runs entirely
on the host.

---

## Disabling credential forwarding

To explicitly disable credential forwarding (e.g. public-only repos):

```yaml
git:
  credential_helper: none
```

`west env doctor` will warn, but builds with public modules will succeed.

---

## Security properties

| Property | Guarantee |
|----------|-----------|
| Private keys in image | Never |
| Tokens in image | Never |
| SSH agent forwarding | Socket bind-mounted read-only (POSIX) |
| Credential manager | Host-side only; no volume mount |
| `git safe.directory` | Always applied (`*`) so west extensions load |
