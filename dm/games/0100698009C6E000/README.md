# Blasphemous (`0100698009C6E000`)

Update 1.0.8 (v524288), The Game Kitchen's Unity 2017.1 / IL2CPP game on NVN, SDK 8.3.1 (NVN API 53.313), with FMOD. The loaded modules are `main`, `subsdk0` (NintendoSDK_movie) and `sdk`. The DLC NSP in the supplied folder is licence-only and contains no game data.

On the Mac, the update boots through its title and opening, reaches the first playable scene, and creates save data. The tested scene renders with its HUD and interaction prompt. The run reached about five minutes; early frame-time p50 was 16.67 ms, while later samples varied between about 16.7 and 34 ms. Resident memory grew from about 1.5 GB at frame 300 to 2.4 GB at frame 10,500 while the opening assets loaded; finalized memory-pool buffers remained at zero. The user reports stable performance on both Mac and iPhone. Their iPhone capture shows an A18 Pro running iOS 27.2 at 59.99 fps with a 16.67 ms frame interval. Sustained story progression and a second boot / load remain unchecked.

## Profile

- `game.tsv` records update 1.0.8 only; the base game and other updates are not separately validated.
- `sys_resource 0x0`: the NPDM declares no system resource, so the game does not use virtual address memory. Its heap request fits the measured 3.25 GB heap region.
- `mem_used 0x7000000`: the rewritten modules are larger than the host's default 64 MB allowance.
- `romfs_marker Data/resources.assets.resS`; packaged data is under `Data/` and `Data/StreamingAssets/`.

## Graphics

The shader split found 605 shaders (301 pixel, 304 vertex); the game's route rendered its title, intro and playable scene on the Mac. Shader maps and facts are the split output for update 1.0.8.

**Open:** Unity's default resources contain `ComputeShader` objects without an available type tree, so `shader_split.py` cannot recover their kernels and reports zero compute shader entries. No compute pipeline was requested on the tested route. Other areas may exercise these shaders; check the host log for a missing compute shader before treating the game as fully covered.

## Mac route

With the Mac host running under `DM_CTL`, press `A` at the title prompt and `A` again to advance the opening. When the prayer menu appears, press `B` to return to the playable scene. Append `shot <path>` to the same control file for a capture. The host created and committed `Save_0.bin` during the run.

The user confirmed that the iOS build launches and separately validated input, audio and haptics. Their performance capture shows an A18 Pro running iOS 27.2 at 59.99 fps with a 16.67 ms frame interval.

## Found on this game

- The SDK's checked offset-table dispatch at `sdk+0xae95f8` appears before its table-base setup in instruction order. The general rewriter now accepts a unique function-wide table candidate only when its bounded entries all target aligned instructions in that function: [Offset-table setup after its dispatch](../../../docs/reference/rewriter.md#offset-table-setup-after-its-dispatch).

## Open

- Recover the default-resource compute shader type tree if a tested area requests one.
- Validate the base build and sustained story progression.
