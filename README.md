# GTA V Populator

![Python](https://img.shields.io/badge/python-3.x-blue)
![GUI](https://img.shields.io/badge/gui-PyQt5-green)
![Platform](https://img.shields.io/badge/platform-Windows-black)

A fast, dark-themed GTA V mod manager built for people who constantly test, swap, break, and rebuild their mod setups.

---

## Overview

GTA V Populator scans your mod folders, detects supported files, groups related assets into bundles, and gives you full control over enabling or disabling mods without touching the original files.

Instead of deleting mods or moving files around manually, Populator simply renames them using `.disabled`, making every change reversible in seconds.

Built for stability, speed, and low-friction troubleshooting.

---

## Features

* Automatic GTA V mod scanning
* Smart mod bundle grouping
* Instant enable / disable system
* Fully reversible mod management
* Category filtering and live search
* Detect newly added mod files
* Minimal blacked-out PyQt5 interface
* No file deletion
* Designed for large mod collections

---

## Why It Exists

Managing GTA V mods manually becomes a mess fast.

Broken dependencies, duplicate files, outdated add-ons, and endless folder digging make troubleshooting painful. GTA V Populator was made to reduce that friction and make mod testing immediate and organized.

The goal is simple:

> See everything. Toggle anything. Break nothing permanently.

---

## How It Works

Mods are never deleted.

Disabling a mod renames its files with:

```text
.disabled
```

Enabling restores the original filenames instantly.

This approach keeps modding safe, transparent, and easy to undo.

---

## Usage

1. Launch the application
2. Add your GTA V root or mod folders
3. Select a category
4. Search or browse detected mod bundles
5. Enable or disable mods instantly
6. Use **Detect New Files** after adding new mods manually

---

## Installation

```bash
git clone <repo>
cd gta-v-populator

pip install -r requirements.txt
python app.py
```

---

## Supported File Types

```text
.asi
.dll
.lua
.rpf
.ini
.meta
.xml
.ymap
.ytyp
.ytd
.yft
```

---

## Tech Stack

* Python 3
* PyQt5
* Windows filesystem APIs

---

## Philosophy

Most mod managers try to automate everything.

GTA V Populator focuses on visibility and control instead.

You decide what loads, what breaks, and what stays disabled. The application simply makes those operations fast and manageable.
