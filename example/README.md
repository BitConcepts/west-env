# west-env Workspace Example

This directory contains a **reference west workspace template** demonstrating
how to use the `west-env` extension correctly.

The `west-env` repository itself is **not** a west workspace.

This example exists to show how a proper workspace should be structured.

Nothing under `example/` is meant to be executed in place or modified.  
Users are expected to **copy the example workspace** to a new location.

---

## What this example provides

* A minimal, correct west workspace layout
* A pinned `west.yml` referencing Zephyr and `west-env`
* A sample `west-env.yml` configuration
* Helper scripts for:
  * bootstrapping the workspace
  * entering a workspace shell
  * running `west-env` commands consistently

This layout mirrors how `west-env` is intended to be used in real projects and CI.

---

## Workspace template layout

```

example/
└─ workspace/
   ├─ west.yml
   ├─ west-env.yml
   └─ scripts/
      ├─ bootstrap.cmd
      ├─ shell.cmd
      ├─ bootstrap.sh
      └─ shell.sh

```

* `west.yml` and `west-env.yml` are **required**
* Scripts assume they are run from the **manifest directory**
* Scripts will fail intentionally if run from an invalid location

---

## Important: west workspace structure (read this)

A **west workspace** consists of two related concepts:

* the **west topdir** — the directory that contains `.west/`
* the **manifest path** — the directory that contains `west.yml`

These may be the same directory or separate directories, as configured by west.

In this example:

* the directory you create (e.g. `west-env-ws/`) becomes the **west topdir**
* the copied `workspace/` directory contains the **manifest (`west.yml`)**
* helper scripts are run from the manifest directory for convenience

Example (correct):

```

west-env-ws/
├─ .west/             ← west topdir
├─ workspace/         ← manifest path
│  ├─ west.yml
│  ├─ west-env.yml
│  └─ scripts/
│     ├─ bootstrap.cmd
│     ├─ shell.cmd
│     ├─ bootstrap.sh
│     └─ shell.sh
├─ zephyr/
└─ modules/
└─ west-env/

````

Although scripts are run from `workspace/`, the **west topdir** is the parent
directory (`west-env-ws/`), as determined by the presence of `.west/`.

The `example/` directory inside the `west-env` repository is **not** a workspace
and must never contain `.west/`, `zephyr/`, or `modules/`.

---

## Creating a workspace from the example

Follow the steps below for your platform.
 
The process is identical conceptually on Windows and POSIX systems.

---

### Windows

#### 1. Create an empty workspace directory

Create a new directory that will become your west workspace.
This directory must be **outside** the `west-env` repository.

```cmd
mkdir C:\work\west-env-ws
cd C:\work\west-env-ws
````

---

#### 2. Copy the example workspace template

From a clone of the `west-env` repository, copy the **contents of
`example\workspace\`** into your new workspace directory.

```cmd
xcopy /E /I C:\src\west-env\example\workspace\* .
```

After copying, your **manifest directory** should contain:

```
workspace/
├─ west.yml
├─ west-env.yml
└─ scripts/
```

---

#### 3. Run bootstrap

From the **manifest directory** (`workspace/`):

```cmd
scripts\bootstrap.cmd
```

This will:

* create a Python virtual environment (`.venv`)
* install `west`
* initialize the west workspace
* fetch required projects
* run `west update`

---

#### 4. Enter the workspace shell

```cmd
scripts\shell.cmd
```

You should see output similar to:

```
Python: vX.Y.Z
West:   vA.B.C
```

You are now in the workspace shell with the correct environment active.

---

### POSIX / Linux / WSL2

#### 1. Create an empty workspace directory

```sh
mkdir ~/west-env-ws
cd ~/west-env-ws
```

---

#### 2. Copy the example workspace template

```sh
cp -r /path/to/west-env/example/workspace .
```

---

#### 3. Run bootstrap

From the **manifest directory** (`workspace/`):

```sh
./scripts/bootstrap.sh
```

---

#### 4. Enter the workspace shell

```sh
./scripts/shell.sh
```

You should now be in the workspace shell with the correct environment active.

---

## Verify the environment

From inside the workspace shell:

```sh
west env doctor
```

All checks should pass before continuing.

---

## Build demo: Zephyr `hello_world`

This example workspace is set up to demonstrate a simple Zephyr build using
`west-env`.

The following command builds the standard **hello_world** sample from the Zephyr
tree.

From inside the workspace shell:

```sh
west env build -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
```

What this does:

* runs `west build` via `west-env`
* executes the build inside the configured container
* builds the `hello_world` application for the Nordic nRF52840 DK
* places build output in the local `build/` directory

---

Here’s the **corrected version of that section**, aligned with how `west-env` actually works and avoiding the misleading implication that flags alone are the primary switch.

You can replace the section verbatim.

---

### Building without the container

To build using the **native host environment**, update your workspace
configuration to disable container execution.

In `west-env.yml`, set:

```yaml
env:
  type: native
````

With container mode disabled in configuration, builds will run directly on the
host by default:

```sh
west env build -b nrf52840dk/nrf52840 ../zephyr/samples/hello_world
```

This uses the same west workspace and build arguments, but executes entirely in
the native host environment.

Note: The `--container` flag can still be used to temporarily override this
configuration and force container execution when needed.


## Notes

* The example workspace is intentionally minimal.
* The workspace directory should **not** be a git repository.
* The example is designed for demonstration and validation.
* Container details are documented separately.

See [`container/README.md`](../container/README.md) for container-specific
information.

---

## Summary

If you remember only one rule:

> **Copy `example/workspace/` into a new directory and work from there.**

This example exists to make the correct usage obvious, reproducible, and aligned
with standard west workflows.
