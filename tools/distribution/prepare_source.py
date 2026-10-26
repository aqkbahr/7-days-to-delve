"""Prepare a reviewable text-source snapshot; omit private archives and binary build products."""
from pathlib import Path
import json,shutil,hashlib

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'artifacts/alpha10/github-source'
assert not OUT.exists(), 'Refuse to mix snapshots'
OUT.mkdir(parents=True)
extensions={'.cs','.py','.ps1','.cmd','.json','.xml','.csv','.txt','.shader','.hlsl'}
for folder in ['src','tools','tests']:
    for p in (ROOT/folder).rglob('*'):
        if p.is_file() and p.suffix.lower() in extensions and '__pycache__' not in p.parts:
            target=OUT/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(p,target)
# Freeze installed configuration alongside the complete source snapshot. Source
# work-in-progress may differ; release/ contains the authoritative tested settings.
package=ROOT/'dist/alpha10/Delve-Alpha-10'
for p in (package/'Mods').rglob('*'):
    if p.is_file() and p.suffix.lower() in {'.xml','.csv','.json','.txt'}:
        target=OUT/'release'/p.relative_to(package);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
for name in ['manifest.json','START-HERE.txt']:
    target=OUT/'release'/name;target.parent.mkdir(exist_ok=True);shutil.copy2(package/name,target)
target=OUT/'docs';target.mkdir()
shutil.copy2(ROOT/'docs/alpha-10-install.txt',target/'alpha-10-install.txt')
shutil.copy2(ROOT/'.gitignore',OUT/'.gitignore')
with (OUT/'.gitignore').open('a') as stream:
    stream.write('\n# Distribution and private local settings\n*.dll\n*.pdb\n*.unity3d\n*.blend1\nlauncher-settings.local.json\n')
(OUT/'README.txt').write_text('''7 DAYS TO DELVE - ALPHA .10

PLAYER DOWNLOAD
https://github.com/aqkbahr/7-days-to-delve/releases/tag/alpha.10
Download Delve-Alpha-10.zip and extract it, then run Play-Delve.cmd.
The automatic Source code ZIP is NOT an installable mod.

Requires Windows and your own Steam installation of 7 Days to Die 3.4.0 (b6),
with the bundled TFP Harmony. Start without Easy Anti-Cheat. The installer checks
the exact supported game assembly. Full instructions: docs/alpha-10-install.txt.

SCOPE AND COMPATIBILITY
Alpha .10 consolidates the selected internal 0.18.1-station-icons build.
All 812 runtime files, 26 modules, art bundles and Allium-v0.10 world files are
preserved byte-for-byte. Internal versions, IDs and alphabetical mod load order
are intentionally unchanged to preserve existing behavior and saves.
This release does not add the rest of the planned overhaul. Human gameplay,
balance and multiplayer acceptance remain incomplete.

REPOSITORY LAYOUT
src/       Development code, configurations and generation inputs.
tools/     Build, content-generation and local validation tools.
tests/     Automated rules and distribution tests.
release/   Frozen Alpha .10 configuration and complete runtime hash manifest.
tools/distribution/  Portable launcher and reproducible release-packaging tools.

The release configuration is authoritative for Alpha .10. Development source may
include earlier or experimental alternatives; do not overlay src/ on a player
installation. The release ZIP includes the matching compiled DLLs and assets.
Binary art authoring projects and generated game/map files are excluded from Git
to keep clones small. The player ZIP supplies all runtime art and world assets.
Some historical developer tools require local build inputs, game files and test
evidence; this repository is not a one-command build of the entire asset pipeline.

UPDATES
Use numbered GitHub Releases. Keep a stable data folder outside extracted
downloads, back up the host's save, close the game and install the chosen version.
Host and clients need the same build. There is no automatic online updater yet.

REPORTING BUGS
Include game/mod versions, steps to reproduce and relevant log excerpts. Remove
passwords, network addresses and personal paths before posting to Issues.
''',encoding='utf-8')
(OUT/'version.json').write_text(json.dumps(dict(displayVersion='Alpha .10',version='alpha.10',
    baselineVersion='0.18.1-station-icons',gameVersion='3.4.0 (b6)',world='Allium-v0.10'),indent=2)+'\n')
entries=[dict(path=p.relative_to(OUT).as_posix(),mode='100644',type='blob',content=p.read_text(encoding='utf-8-sig'))
         for p in sorted(OUT.rglob('*')) if p.is_file()]
(ROOT/'artifacts/alpha10/github-tree.json').write_text(json.dumps(entries,ensure_ascii=True),encoding='ascii')
manifest=[dict(path=e['path'],sha256=hashlib.sha256(e['content'].encode()).hexdigest()) for e in entries]
(ROOT/'artifacts/alpha10/github-source-hashes.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(files=len(entries),jsonCharacters=(ROOT/'artifacts/alpha10/github-tree.json').stat().st_size)))
