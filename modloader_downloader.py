import requests
import subprocess
import json
import sys
import os
import glob

SUPPORTED_MODLOADERS = ['fabric-loader', 'forge', 'quilt-loader', 'neoforge']

def download_modloader(modloader, loader_version, minecraft_version):
    """The only function that needs to be called in this module.
    Downloads the modloader specified by modloader and version to cwd/server.
    Then, write the start script for the server."""

    match modloader:
        case 'minecraft':
            _download_minecraft(minecraft_version)
        case 'fabric-loader':
            _download_fabric(loader_version, minecraft_version)
        case 'forge':
            _download_forge(minecraft_version)
        case 'quilt-loader':
            _download_quilt(loader_version, minecraft_version)
        case 'neoforge':
            _download_neoforge(loader_version)
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

    _write_jar_start_script('server.jar')

def _download_fabric(loader_version, minecraft_version):
    # Download installer
    fabric_installer_url = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/1.0.1/fabric-installer-1.0.1.jar"
    fabric_installer_req = requests.get(fabric_installer_url)
    with open('fabric-installer.jar', 'wb') as fabric_installer_jar:
        fabric_installer_jar.write(fabric_installer_req.content)

    # Install fabric
    subprocess.run(['java', '-jar', 'fabric-installer.jar', 'server', '-snapshots', '-dir', 'server', '-loader', loader_version, '-mcversion', minecraft_version, '-downloadMinecraft'], check=True)
    _write_jar_start_script('fabric-server-launch.jar')

def _download_forge(minecraft_version):
    # Download from mctools TODO: Update to a better source
    forge_url = f"https://mcutils.com/api/server-jars/forge/{minecraft_version}/download"
    forge_req = requests.get(forge_url)
    with open('forge-installer.jar', 'wb') as forge_jar:
        forge_jar.write(forge_req.content)

    # Install forge
    subprocess.run(['java', '-jar', '../forge-installer.jar', '--installServer'], cwd="server", check=True)

    # Figure out where the server jar is
    forge_jars = glob.glob('server/forge-*.jar')
    if len(forge_jars) != 1:
        sys.exit("Couldn't find the forge server jar.")

    forge_jar = forge_jars[0]
    _write_jar_start_script(forge_jar.split('/')[-1])

def _download_quilt(loader_version, minecraft_version):
    # Download quilt installer
    quilt_installer_url = "https://quiltmc.org/api/v1/download-latest-installer/java-universal"
    quilt_installer_req = requests.get(quilt_installer_url)
    with open('quilt-installer.jar', 'wb') as quilt_installer_jar:
        quilt_installer_jar.write(quilt_installer_req.content)

    # Install quilt
    subprocess.run(['java', '-jar', 'quilt-installer.jar', 'install', 'server', minecraft_version, loader_version, '--install-dir=server', '--download-server'], check=True)
    _write_jar_start_script('quilt-server-launch.jar')

def _download_neoforge(loader_version):
    # Download neoforge installer
    neoforge_installer_url = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{loader_version}/neoforge-{loader_version}-installer.jar"
    neoforge_installer_req = requests.get(neoforge_installer_url)
    with open('neoforge-installer.jar', 'wb') as neoforge_installer_jar:
        neoforge_installer_jar.write(neoforge_installer_req.content)

    # Install neoforge
    subprocess.run(['java', '-jar', 'neoforge-installer.jar', '--install-server', 'server'], check=True)

    # Replace start scripts
    os.remove('server/run.sh')
    os.remove('server/run.bat')
    os.remove('server/user_jvm_args.txt')
    _write_start_script(f'@libraries/net/neoforged/neoforge/{loader_version}/unix_args.txt nogui "$@"')

def _write_start_script(launch_command):
    # Gather Additional Arguments
    max_memory = os.environ.get("MAX_RAM", "4G")
    min_memory = os.environ.get("MIN_RAM", "2G")
    typical_args = os.environ.get("TYPICAL_START_ARGS", "-XX:+UnlockExperimentalVMOptions -XX:+UseG1GC -XX:G1NewSizePercent=20 -XX:G1ReservePercent=20 -XX:MaxGCPauseMillis=50 -XX:G1HeapRegionSize=32M")
    additional_args = os.environ.get("ADDITIONAL_START_ARGS", "")

    start_script = f"#!/bin/sh\njava -server -Xmx{max_memory} -Xms{min_memory} {typical_args} {additional_args} {launch_command}"
    with open('server/start.sh', 'w') as start_script_file:
        start_script_file.write(start_script)
    os.chmod('server/start.sh', 0o744)

def _write_jar_start_script(jar_file):
    _write_start_script(f"-jar {jar_file} nogui")
