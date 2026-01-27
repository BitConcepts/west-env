# west-env Workspace Example

This directory contains a **reference west workspace template** demonstrating
how to use the `west-env` extension correctly.

> The `west-env` repository itself is **not** a west workspace.
> This example exists to show how a proper workspace should be structured.

Nothing under `example/` is meant to be executed in place or modified.  
Users are expected to **copy the example workspace** to a new location.

---

## What this example provides

* A minimal, correct west workspace layout
* A pinned `west.yml` referencing Zephyr and `west-env`
* A sample `west-env.yml` configuration
* Windows helper scripts for:
  * bootstrapping the workspace
  * entering the workspace shell
  * validating setup (round-trip tests)

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
      ├─ test-roundtrip.cmd
      └─ test-roundtrip-container.cmd

````

* `west.yml` and `west-env.yml` are **required**
* Scripts assume they are run from the **workspace root**
* Scripts will fail intentionally if run from an invalid location

---

## Windows: Creating a workspace from the example

### 1. Create an empty workspace directory

Create a new directory that will become your west workspace.
This directory must be outside the `west-env` repository.

For example:

```cmd
mkdir C:\work\west-env-ws
cd C:\work\west-env-ws
````

This directory will become your west workspace root.

---

### 2. Copy the example workspace template

From a clone of the `west-env` repository, copy the **`example\workspace\`**
directory into your new workspace directory.

For example, if `west-env` is cloned at `C:\src\west-env`:

```cmd
xcopy /E /I C:\src\west-env\example\workspace\* .
```

After copying, your workspace root should contain:

```
west-env-ws/
├─ west.yml
├─ west-env.yml
└─ scripts/
```

---

### 3. Run bootstrap

From the workspace root:

```cmd
scripts\bootstrap.cmd
```

This will:

* create a Python virtual environment (`.venv`)
* install `west`
* initialize the west workspace
* fetch required projects
* run `west update`

The script will fail if:

* run from the wrong directory
* run inside a git repository
* required files (`west.yml`) are missing

---

### 4. Enter the workspace shell

```cmd
scripts\shell.cmd
```

You should see output similar to:

```
Python: vX.Y.Z
West:   vA.B.C
```

You are now in the workspace root with the correct environment active.

---

### 5. Verify installation

```cmd
west env doctor
```

If this succeeds, the workspace and `west-env` extension are correctly configured.

---

## Notes

* The example workspace is intentionally minimal.
* The workspace directory should **not** be a git repository.
* Additional projects (e.g. Zephyr itself) may be added to `west.yml` as needed.
* The scripts under `scripts/` are **reference helpers**, not part of the core
  `west-env` functionality.

---

## Summary

If you remember only one rule:

> **Copy `example/workspace/` into a new directory and work from there.**
> Do not try to turn the `west-env` repository itself into a workspace.

This example exists to make the correct usage obvious and reproducible.
