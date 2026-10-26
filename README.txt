7 DAYS TO DELVE - ALPHA .10

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
