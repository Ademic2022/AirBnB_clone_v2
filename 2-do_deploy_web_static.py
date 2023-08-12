#!/usr/bin/python3
"""
Fabric script that distributes an archive to your web servers, using the function do_deploy
"""

from fabric.api import *
from datetime import datetime
import os

env.hosts = ['54.157.32.137', '52.55.249.213']  # List of IP addresses or hostnames of your servers
env.user = 'ubuntu'  # SSH username
env.key_filename = '~/.ssh/id_rsa'  # Path to your SSH private key

def do_pack():
    """
    Generates a .tgz archive from the contents of the web_static folder
    Returns: Archive path if successful, None otherwise
    """
    try:
        now = datetime.now().strftime('%Y%m%d%H%M%S')
        archive_file = 'versions/web_static_' + now + '.tgz'
        local('mkdir -p versions')
        local('tar -cvzf {} web_static'.format(archive_file))
        return archive_file
    except:
        return None

def do_deploy(archive_path):
    """
    Distributes an archive to your web servers
    Args:
        archive_path: Path to the archive file
    Returns: True if successful, False otherwise
    """
    if not os.path.exists(archive_path):
        return False

    try:
        archive_filename = os.path.basename(archive_path)
        archive_no_extension = os.path.splitext(archive_filename)[0]
        release_path = '/data/web_static/releases/' + archive_no_extension

        # Upload the archive to the /tmp/ directory on the remote server
        put(archive_path, '/tmp/')

        # Create the release directory
        run('sudo mkdir -p {}'.format(release_path))

        # Extract the contents of the archive into the release directory
        run('sudo tar -xzf /tmp/{} -C {}'.format(archive_filename, release_path))

        # Delete the uploaded archive
        run('sudo rm /tmp/{}'.format(archive_filename))

        # Use rsync to move files from the nested web_static directory to the release directory
        run('sudo rsync -av --delete {}/web_static/ {}/'.format(release_path, release_path))

        # Delete the empty nested web_static directory
        run('sudo rm -rf {}/web_static'.format(release_path))

        # Update the symbolic link to the new release
        run('sudo rm -rf /data/web_static/current')
        run('sudo ln -s {} /data/web_static/current'.format(release_path))

        print("New version deployed!")
        return True
    except:
        return False

