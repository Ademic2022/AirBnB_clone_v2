#!/usr/bin/python3
"""Deploy and clean up outdated archives."""
import os
import re
from datetime import datetime
from fabric.api import env, local, put, run, runs_once

# Update the list of hosts
env.hosts = ['34.138.32.248', '3.226.74.205']

@runs_once
def do_pack():
    """Archives the static files."""
    if not os.path.isdir("versions"):
        os.mkdir("versions")
    cur_time = datetime.now()
    output = "versions/web_static_{}{}{}{}{}{}.tgz".format(
        cur_time.year,
        cur_time.month,
        cur_time.day,
        cur_time.hour,
        cur_time.minute,
        cur_time.second
    )
    try:
        print("Packing web_static to {}".format(output))
        local("tar -cvzf {} web_static".format(output))
        archize_size = os.stat(output).st_size
        print("web_static packed: {} -> {} Bytes".format(output, archize_size))
    except Exception:
        output = None
    return output

def do_deploy(archive_path):
    """Deploys the static files to the host servers."""
    if not os.path.exists(archive_path):
        return False
    file_name = os.path.basename(archive_path)
    folder_name = file_name.replace(".tgz", "")
    folder_path = "/data/web_static/releases/{}/".format(folder_name)
    success = False
    try:
        put(archive_path, "/tmp/{}".format(file_name))
        run("mkdir -p {}".format(folder_path))
        run("tar -xzf /tmp/{} -C {}".format(file_name, folder_path))
        run("rm -rf /tmp/{}".format(file_name))
        run("mv {}web_static/* {}".format(folder_path, folder_path))
        run("rm -rf {}web_static".format(folder_path))
        run("rm -rf /data/web_static/current")
        run("ln -s {} /data/web_static/current".format(folder_path))
        print('New version deployed!')
        success = True
    except Exception:
        success = False
    return success

def deploy():
    """Archives and deploys the static files to the host servers."""
    archive_path = do_pack()
    return do_deploy(archive_path) if archive_path else False

def do_clean(number=0):
    """Deletes out-of-date archives and releases."""
    number = int(number)
    if number < 0:
        return
    archives = os.listdir('versions/')
    archives.sort(reverse=True)
    if number == 0:
        # Keep the latest
        number = 1
    else:
        number += 1

    # Delete outdated archives
    for archive in archives[number:]:
        os.unlink('versions/{}'.format(archive))

    # Remove outdated releases on the server
    path = '/data/web_static/releases'
    releases = run('ls -1t {} | grep web_static'.format(path))
    releases_list = re.findall(r'web_static_\d{14}', releases)
    if len(releases_list) > number:
        for release in releases_list[number:]:
            run('rm -rf {}/{}'.format(path, release))

# Ensure both deploy and do_clean are available
@runs_once
def full_deploy_and_clean():
    """Full deployment and clean-up."""
    deployed = deploy()
    cleaned = do_clean(2)  # Keep the latest 2 versions
    return deployed and cleaned
