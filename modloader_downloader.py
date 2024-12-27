import requests
import subprocess
import json
import sys
import os
import glob

SUPPORTED_MODLOADERS = ['fabric', 'forge', 'quilt-loader', 'neoforge']

def download_modloader(modloader, version, minecraft_version):
    """The only function that needs to be called in this module.
    Downloads the modloader specified by modloader and version to cwd/server.
    Then, write the start script for the server."""

    match modloader:
        case 'minecraft':
            _download_minecraft(minecraft_version)
        # case 'fabric':
        #     download_fabric(version)
        case 'forge':
            _download_forge(minecraft_version)
        # case 'quilt-loader':
        #     download_quilt(version)
        # case 'neoforge':
        #     download_neoforge(version)
        case _:
            raise ValueError(f"Unsupported modloader: {modloader}")

def _download_minecraft(minecraft_version):
    # Download the minecraft server jar
    minecraft_versions_url = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
    minecraft_versions_req = requests.get(minecraft_versions_url)
    minecraft_versions = json.loads(minecraft_versions_req.content)
    minecraft_version_url = None
    for version in minecraft_versions['versions']:
        if version['id'] == minecraft_version:
            minecraft_version_url = version['url']
            break
    if minecraft_version_url is None:
        sys.exit("Couldn't find the minecraft server version specified in mrpack.")
    minecraft_server_version_req = requests.get(minecraft_version_url)
    minecraft_server_version_downloads = json.loads(minecraft_server_version_req.content)
    minecraft_server_download_url = minecraft_server_version_downloads['downloads']['server']['url']
    minecraft_server_jar_req = requests.get(minecraft_server_download_url)
    with open('server/server.jar', 'wb') as minecraft_server_jar:
        minecraft_server_jar.write(minecraft_server_jar_req.content)

    _write_start_script('server.jar')

def _download_forge(minecraft_version):
    # Download from mctools
    forge_url = f"https://mcutils.com/api/server-jars/forge/{minecraft_version}/download"
    forge_req = requests.get(forge_url)
    with open('forge-installer.jar', 'wb') as forge_jar:
        forge_jar.write(forge_req.content)

    # Install forge
    subprocess.run(['java', '-jar', 'forge-installer.jar', '--installServer'], cwd="server", check=True)

    # Remove log file and figure out where the server jar is
    forge_jars = glob.glob('server/forge-*.jar')
    if len(forge_jars) != 1:
        sys.exit("Couldn't find the forge server jar.")

    forge_jar = forge_jars[0]
    install_log = forge_jar[:-4] + "-installer.jar.log"
    os.remove(install_log)
    _write_start_script(forge_jar)

def _write_start_script(jar_file):
    # Gather Additional Arguments
    max_memory = os.environ.get("MAX_RAM", "4G")
    min_memory = os.environ.get("MIN_RAM", "2G")
    typical_args = os.environ.get("TYPICAL_START_ARGS", "-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M")
    additional_args = os.environ.get("ADDITIONAL_START_ARGS", "")

    start_script = f"#!/bin/sh\njava -server -Xmx{max_memory} -Xms{min_memory} {typical_args} {additional_args} -jar {jar_file} nogui"
    with open('server/start.sh', 'w') as start_script_file:
        start_script_file.write(start_script)
    os.chmod('start.sh', 0o744)
