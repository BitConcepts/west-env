# west-env Workspace Example

This directory contains **reference scripts** demonstrating how to set up a
clean west workspace and integrate the `west-env` extension.

These scripts are intentionally placed under `example/` to avoid confusion:
the `west-env` repository itself is **not** a west workspace.

---

## What this example provides

* A clean, reproducible west workspace
* A Python virtual environment for tooling
* Automatic integration of `west-env` as a west extension
* A safe reference for local testing and CI

---

## Windows: Workspace Bootstrap

### 1. Create a new workspace directory

Choose or create a directory that will act as your west workspace:

```cmd
mkdir west-env-ws
cd west-env-ws
```

This directory will become the workspace root.

---

### 2. Copy the example scripts into the workspace

From the `example/` directory, copy the scripts into your workspace root:

```cmd
copy example\workspace\bootstrap.cmd .
copy example\workspace\shell.cmd .
copy example\workspace\test-roundtrip.cmd .
```

> These scripts **must be run from the workspace root**.

---

### 3. Run bootstrap

```cmd
bootstrap.cmd
```

This will:

* create a Python virtual environment (`.venv`)
* install `west`
* generate a minimal `west.yml`
* fetch `west-env` into `modules/west-env`
* initialize the west workspace
* run `west update`

The script will fail intentionally if run from an invalid location.

---

### 4. Enter the workspace shell

```cmd
shell.cmd
```

You should see output similar to:

```
Python: vX.Y.Z
West: vA.B.C
```

You are now in the workspace root with the correct environment activated.

---

### 5. Verify installation

```cmd
west env doctor
```

If this succeeds, the workspace is correctly configured and `west-env`
is available.

---

## Expected workspace layout

After a successful bootstrap, the workspace should look like this:

```
west-env-ws/
├─ .venv/
├─ .west/
├─ west.yml
├─ bootstrap.cmd
├─ shell.cmd
├─ test-roundtrip.cmd
└─ modules/
   └─ west-env/
```

## Quick start (Windows)

You need the example scripts from the `west-env` repository. A brand-new workspace
directory won’t have `example\workspace\bootstrap.cmd` until you either clone the
repo or download/copy the scripts into the workspace.

### Option A (recommended): clone the repo, then copy scripts into the workspace

```cmd
mkdir west-env-ws
cd west-env-ws

git clone https://github.com/bitconcepts/west-env modules\west-env

copy modules\west-env\example\workspace\bootstrap.cmd .
copy modules\west-env\example\workspace\shell.cmd .
copy modules\west-env\example\workspace\test-roundtrip.cmd .

bootstrap.cmd
shell.cmd
west env doctor
````

### Option B: if you already have a local `west-env` repo checkout

Replace `C:\path\to\west-env` with your local repo path:

```cmd
mkdir west-env-ws
cd west-env-ws

copy C:\path\to\west-env\example\workspace\bootstrap.cmd .
copy C:\path\to\west-env\example\workspace\shell.cmd .
copy C:\path\to\west-env\example\workspace\test-roundtrip.cmd .

bootstrap.cmd
shell.cmd
west env doctor
```
