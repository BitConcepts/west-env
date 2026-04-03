<!-- SPDX-License-Identifier: Apache-2.0 -->

# west-env Workspace Example

This directory contains a reference workspace template for `west-env`.
Use it as a template, not as a live workspace inside this repository.
Copy the contents of `example/workspace/` into a new directory and work there.

## Key idea

Operate in the copied workspace.
Treat the `west-env` repository as extension source only.

That means:

* this repository should stay free of `.west/`, `zephyr/`, `modules/`, `.venv/`, and build output
* your copied workspace becomes the west topdir and manifest location
* bootstrap, shell, doctor, and build commands should be run from that copied workspace root

## Workspace layout

Before bootstrap, your new workspace root should look like this:

```text
west-env-ws/
├─ west.yml
├─ west-env.yml
└─ scripts/
   ├─ bootstrap.cmd
   ├─ bootstrap.sh
   ├─ shell.cmd
   └─ shell.sh
```

After bootstrap and `west update`, it will typically look like this:

```text
west-env-ws/
├─ .west/
├─ .venv/
├─ west.yml
├─ west-env.yml
├─ scripts/
├─ zephyr/
└─ modules/
   └─ west-env/
```

## Create a workspace

### Windows

```cmd
mkdir C:\work\west-env-ws
xcopy /E /I C:\src\west-env\example\workspace\* C:\work\west-env-ws\
cd /d C:\work\west-env-ws
scripts\bootstrap.cmd
scripts\shell.cmd
```

### POSIX / Linux / WSL2

```sh
mkdir -p ~/west-env-ws
cp -r /path/to/west-env/example/workspace/. ~/west-env-ws/
cd ~/west-env-ws
./scripts/bootstrap.sh
./scripts/shell.sh
```

## What bootstrap does

The bootstrap script is responsible for:

* creating the workspace virtual environment
* installing `west`
* initializing the workspace if needed
* running `west update`
* installing Zephyr Python dependencies from the checked-out Zephyr tree

## Verify the environment

From the workspace root or workspace shell:

```sh
west env doctor
```

What `doctor` should confirm:

* Python is available
* `west` is installed
* the selected container engine is available when container mode is enabled
* the configured image exists locally or can be pulled later
* the mounted workspace looks valid inside the container

## Build a sample

Container-backed build:

```sh
west env build -b native_sim zephyr/samples/hello_world
```

Native build after changing `west-env.yml` to `env.type: native`:

```sh
west env build -b native_sim zephyr/samples/hello_world
```

If you switch between native and container builds, remove the old build
directory first to avoid stale CMake cache paths.

## Recommended first-time flow

1. Copy `example/workspace/` into a new directory.
2. Run the bootstrap script.
3. Open the workspace shell.
4. Run `west env doctor`.
5. Build `zephyr/samples/hello_world` in the default mode.
6. Switch modes only after deleting the previous `build/` directory.

## Common mistakes

Avoid these:

* running the example in place inside the `west-env` repository
* copying `example/` instead of the contents of `example/workspace/`
* creating `.west/` inside the extension repository
* expecting the container image to contain the workspace
* reusing a build directory after changing execution mode
* treating the extension repository as if it were the actual project workspace
