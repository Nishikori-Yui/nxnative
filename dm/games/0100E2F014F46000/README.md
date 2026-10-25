# NINJA GAIDEN Σ (`0100E2F014F46000`)

Update 1.0.2 (v131072) over the base game, SDK 10.9.0. Team Ninja's engine on NVN. Modules `main`, `subsdk0` (NintendoSDK_movie) and `sdk`.

Status: plays on the iPhone (A18 Pro, iOS 27.2, 2346x1320), at about 59.5 fps (16.81 ms frame interval, 7.25 ms GPU time); the performance overlay reported 1.71 GB of Metal allocations and 1.08 GB of app memory. On the Mac: Chapter 1 gameplay with movement and camera control, at about 60 fps on an Apple M5 Max.

## What it needs

| Setting | Where | Why |
|---|---|---|
| `pad_layout full` | [`game.tsv`](game.tsv) | starts the iPhone's virtual gamepad in 3D, with the right stick for the camera |
| 4 GB layout: `mem_reserve 0x100000000`, `mem_alias 0x10000000`, `mem_stack 0x10000000`, `app_pool 0xCD500000` | `game.tsv` | no virtual address memory in the NPDM; the game sets its heap from the application pool |
| `sys_resource 0x0` | `game.tsv` | the NPDM declares no system resource, so `IsVirtualAddressMemoryEnabled` is false, as on Horizon |
| `mem_used 0x5c00000` (92 MB) | `game.tsv` | the rewritten modules exceed the default 64 MB reported as used memory |
| `shader_groups /databin/=databin /patchbin/=patchbin` | `game.tsv` | the game's GLSLC shader programs are in these indexed zlib archives; see [Files and shaders](#files-and-shaders) |

## Files and shaders

The RomFS has 550 files (3.25 GB): 530 sound files, 17 MP4 movies, `databin/databin` and `patchbin/patchbin`. The two Team Ninja archives use an index of records containing zlib streams. `databin.py` reads and bounds-checks the index and verifies each decoded member's size; `shader_split.py` scans the shader-bearing entries rather than treating each archive as one GLSLC blob.

The current split has 1,296 GLSLC programs (467 vertex and 829 pixel): 1,283 from the archives and 13 from `main`. The vertex/pixel pairs table has 467 rows. No compute programs or manually supplied shader facts were found. The prewarm manifest is empty, so the first use of an unrecorded pipeline can compile on demand.

## Filesystem

SDK 10.9.0 calls `nn::fs::ReadFile(FileHandle, offset, buffer, length, ReadOption)`. The SDK implementation expects its own `FileAccessor`, but the host's handle is a file descriptor. `hle_fs.c` takes over that overload and uses the host's exact-read implementation, which rejects short reads. `t_fs` covers offset/length reads, short reads and an invalid handle.

## Mac routes

The route used for verification reached Chapter 1 gameplay, where Ryu, the environment and HUD were visible and the left/right stick controls were usable. The opening, later chapters and save creation/loading remain unverified.

## Found on this game

- **Indexed Team Ninja shader archives** (`databin.py`, `databin_jobs` in `shader_split.py`): covered by `dm/gfx/tests/test_databin.py` with fixtures for payload padding, bounds, malformed members and unrelated formats.
- **SDK 10.9.0 `ReadFile` overload with `ReadOption`** (`hle_fs.c`): regression checks in `dm/host/tests/t_fs.c`.

## Open

- The `pso_manifest.tsv` is empty; it has not been recorded over a full play route.
- Only Chapter 1 gameplay has been checked on the Mac. On the iPhone, gameplay and performance have been checked, but save/load and later chapters have not.
