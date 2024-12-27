# Modpack Server Downloader/Runner
This (primarily) docker based project downloads all the files necessary to run a modpack minecraft server.
It uses modrinth as the primary backend to locate mods and will download the appropriate modloader and server jars.

The way this will work is docker will first obtain a mrpack file from either a local directory or via mod id/slug from modrinth.
It will extract the mrpack file and then download the remaining files from modrinth.
Next, it will download the correct modloader and server jars.
Finally, it will copy the files into a clean docker base image.
From there the docker image will be configured to automatically run the modded server on start.

## Usage
Set the following build arguments via `--build-arg [ARG]=[VAL]`:
- Set `MRPACK_FILE` to the location of the mrpack file (must be within the build context), `MRPACK_VERSION` to a specific version id of the modpack or `MRPACK_ID` to the modrinth id/slug (which downloads the latest version). (Priority: File, Version, ID)
- Optionally set `MAX_RAM` and `MIN_RAM` same as setting `-Xmx` and `-Xms` in the Java command. (Default: 2G-4G)
- Optionally set `INSTALL_OPTIONAL_MODS` to `0` if you don't want to install optional mods. (Default: 1)

To ensure your minecraft server doesn't delete itself when the container stops, mount a volume to `/data`.
Note that the volume will only store world data and configuration files, the data on the volume is symlinked to the actual server directory.
