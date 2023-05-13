#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path

#####################################################################

##
## The name of the modified kernel package.
##
PACKAGE_NAME = "surface"

##
## https://gitlab.com/cki-project/kernel-ark/-/tags
##
## Fedora tags: kernel-X.Y.Z
## Upstream tags: vX.Y.Z
##
PACKAGE_TAG = "kernel-6.3.6-0"

##
## The release number of the modified kernel package.
## e.g. 300 for kernel-6.3.1-300.fc38.foo
##
PACKAGE_RELEASE = "1"

##
## Build options for configuring which parts of the kernel package are enabled.
##
## We disable all userspace components because we only want the kernel + modules.
## We also don't care too much about debug info or UKI.
##
## To list the available options, run make dist-full-help in the kernel-ark tree.
##
KERNEL_BUILDOPTS = "+up +baseonly -debuginfo -doc -headers -efiuki"

#####################################################################

# The directory where this script is saved.
script = Path(sys.argv[0]).resolve().parent

# The root of the linux-surface repository.
linux_surface = script / ".." / ".." / ".."

# Determine the major version of the kernel.
kernel_version = PACKAGE_TAG.split("-")[1]
kernel_major = ".".join(kernel_version.split(".")[:2])

# Determine the patches directory and config file.
patches = linux_surface / "patches" / kernel_major
config = linux_surface / "configs" / ("surface-%s.config" % kernel_major)

sb_cert = script / "secureboot" / "MOK.crt"
sb_key = script / "secureboot" / "MOK.key"

# Check if the major version is supported.
if not patches.exists() or not config.exists():
    print("ERROR: Could not find patches / configs for kernel %s!" % kernel_major)
    sys.exit(1)

# Check if Secure Boot keys are available.
sb_avail = sb_cert.exists() and sb_key.exists()

# If we are building without secureboot, require user input to continue.
if not sb_avail:
    print("")
    print("Secure Boot keys were not configured! Using Red Hat testkeys.")
    print("The compiled kernel will not boot with Secure Boot enabled!")
    print("")

    input("Press any key to continue")

# Expand globs
surface_patches = list(patches.glob("*.patch"))

cmd = []
cmd += [script / "build-ark.py"]
cmd += ["--package-name", PACKAGE_NAME]
cmd += ["--package-tag", PACKAGE_TAG]
cmd += ["--package-release", PACKAGE_RELEASE]
cmd += ["--patch"] + surface_patches
cmd += ["--config", config]
cmd += ["--buildopts", KERNEL_BUILDOPTS]

local_patches = list((script / "patches").glob("*.patch"))
local_configs = list((script / "configs").glob("*.config"))
local_files = list((script / "files").glob("*"))

if len(local_patches) > 0:
    cmd += ["--patch"] + local_patches

if len(local_configs) > 0:
    cmd += ["--config"] + local_configs

if len(local_files) > 0:
    cmd += ["--file"] + local_files

if sb_avail:
    sb_patches = list((script / "secureboot").glob("*.patch"))
    sb_configs = list((script / "secureboot").glob("*.config"))

    if len(sb_patches) > 0:
        cmd += ["--patch"] + sb_patches

    if len(sb_configs) > 0:
        cmd += ["--config"] + sb_configs

    cmd += ["--file", sb_cert, sb_key]

subprocess.run(cmd, check=True)
