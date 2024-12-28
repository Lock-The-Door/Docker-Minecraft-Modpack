import sys
import os
import zipfile as zip
import json
import requests
from logging import warning
import modloader_downloader
import shutil

def main():
    # Grab the first argument as the action to take
    action = sys.argv[1]

    match action:
        case 'mrpack':
            if os.path.isfile('modpack.mrpack'):
                print('Modpack already available. Skipping download...')
            else:
                if os.path.exists('modpack.mrpack'):
                    os.remove('modpack.mrpack')
                download_mrpack(sys.argv[2])
            extract_mrpack()
        case 'mods':
            os.makedirs('server', exist_ok=True)
            download_mods()
        case 'server':
            download_server()
        case _:
            sys.exit('Invalid action provided. Exiting...')

def download_mrpack(mrpack_source):
    # Validate the type of source. The docker builder will copy the modpack to modpack.mrpack if available.
    project_url = f"https://api.modrinth.com/v2/project/{mrpack_source}"
    version_url = f"https://api.modrinth.com/v2/version/{mrpack_source}"
    project_req = requests.get(project_url)
    if project_req.status_code == 200:
        project = project_req.json()
        version_url = f"https://api.modrinth.com/v2/version/{project['versions'][-1]}"

    version_req = requests.get(version_url)
    if version_req.status_code != 200:
        sys.exit(f"Couldn't find the modpack with the source provided: {mrpack_source}")
    version = version_req.json()
    version_downloads = version['files']
    download_url = None
    for download in version_downloads:
        if download['primary']:
            download_url = download['url']
            break
    if download_url is None:
        sys.exit(f"Couldn't find the primary download for the modpack with the source provided: {mrpack_source}")

    download_req = requests.get(download_url)
    with open('modpack.mrpack', 'wb') as modpack_file:
        modpack_file.write(download_req.content)

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

    # Copy over overrides directory if it exists
    # try:
        # for file in os.listdir("overrides"):
        shutil.copytree("overrides", "server", dirs_exist_ok=True)
    # except:
    #     print("No overrides folder to copy")

    # Return the modpack name and version
    return f"{modrinth_index['name']} {modrinth_index['versionId']}"

RECOMMENDED_JAVA_VERSIONS = {
    0: 'openjdk8-jre-base', # Default
    17: 'openjdk17-jre-headless',
    20: 'openjdk21-jre-headless'
}
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
        warning('No modloader found in dependencies.')
        modloader_downloader.download_modloader('minecraft', None, minecraft_version)
    else:
        modloader_downloader.download_modloader(modloader, modloader_version, minecraft_version)

    # Save the recommended alpine java package to the server folder
    with open('java-version', 'w') as recommended_java:
        # For versions 1.16.5 and below, use openjdk8-jre-base, otherwise use openjdk17-jre-headless
        minor_version = int(minecraft_version.split('.')[1])
        recommended_java_version = RECOMMENDED_JAVA_VERSIONS[0]
        for version in RECOMMENDED_JAVA_VERSIONS:
            if minor_version >= version:
                recommended_java_version = RECOMMENDED_JAVA_VERSIONS[version]
            else:
                break
        recommended_java.write(recommended_java_version)

    return f"{modloader}-{modloader_version} for {minecraft_version}"

if __name__ == '__main__':
    main()
