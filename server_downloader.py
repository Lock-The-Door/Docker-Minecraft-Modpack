import sys
import os
import zipfile as zip
import json
import requests
from logging import warn
import modloader_downloader

def main():
    # Grab the first argument as the action to take
    action = sys.argv[1]

    match action:
        case 'mrpack':
            if os.path.exists('modpack.mrpack'):
                print('Modpack already available. Skipping download...')
            else:
                download_mrpack(sys.argv[2])
            extract_mrpack()
        case 'mods':
            os.mkdir('server')
            download_mods()
        case 'server':
            download_server()
        case _:
            sys.exit('Invalid action provided. Exiting...')

def download_mrpack(mrpack_source):
    # Validate the type of source. The docker builder will copy the modpack to modpack.mrpack if available.
    pass
def extract_mrpack():
    # Extract the mrpack to the current directory as a zip file
    zip.ZipFile('modpack.mrpack').extractall()
    # There is now an overrides folder and a modrinth.index.json file.
def download_mods():
    # Reads the mrpack to figure out remaining mods to download from modrinth.
    # Returns a string with the listed modpack name and version.
    json_file = open('modrinth.index.json')
    modrinth_index = json.load(json_file)
    json_file.close()

    mod_list = modrinth_index['files']
    for mod in mod_list:
        requirement = mod["env"]["server"]
        should_download = requirement == 'required' or (requirement == 'optional' and os.environ["INSTALL_OPTIONAL_MODS"] == "1")
        if not should_download:
            continue

        download_url = mod["downloads"][0]
        # Download the mod to the server folder
        download_req = requests.get(download_url)
        os.makedirs('server/' + os.path.dirname(mod["path"]), exist_ok=True)
        with open(f'server/{mod["path"]}', 'wb') as mod_file:
            mod_file.write(download_req.content)

        # Verify the mod hash
        # TODO: Implement hash verification

    # Return the modpack name and version
    return f"{modrinth_index['name']} {modrinth_index['versionId']}"

def download_server():
    # Reads the mrpack and figures out the appropriate modloader and server version to download.
    # Returns a string that represents the modloader and server version.
    json_file = open('modrinth.index.json')
    modrinth_index = json.load(json_file)
    json_file.close()

    dependencies = modrinth_index['dependencies']
    minecraft_version = dependencies['minecraft']
    # search through keys to figure out appropriate modloader
    modloader = None
    modloader_version = None
    for supported_modloader in modloader_downloader.SUPPORTED_MODLOADERS:
        if supported_modloader in dependencies:
            modloader = supported_modloader
            modloader_version = dependencies[supported_modloader]
            break

    if modloader is None:
        warn('No modloader found in dependencies.')
        modloader_downloader.download_modloader('minecraft', None, minecraft_version)
    else:
        modloader_downloader.download_modloader(modloader, modloader_version, minecraft_version)

    # Save the recommended alpine java package to the server folder
    with open('server/java-version', 'w') as recommended_java:
        # For versions 1.16.5 and below, use openjdk8-jre-base, otherwise use openjdk17-jre-headless
        minor_version = int(minecraft_version.split('.')[1])
        recommended_java.write('openjdk8-jre-base' if minor_version <= 16 else 'openjdk17-jre-headless')

    return f"{modloader}-{modloader_version} for {minecraft_version}"

if __name__ == '__main__':
    main()