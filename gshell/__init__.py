#!/usr/bin/env python

from __future__ import print_function

from collections import deque
import os
import pkg_resources
import platform
import re
import subprocess
import sys
import yaml

import click


__author__ = 'Kentaro Wada <www.kentaro.wada@gmail.com>'
__version__ = pkg_resources.get_distribution('gshell').version


this_dir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
CONFIG_FILE = os.path.expanduser('~/.gshell')
if platform.uname()[0] == 'Linux':
    DRIVE_EXE = os.path.join(this_dir, 'bin/_gshell_drive-linux-x64')
elif platform.uname()[0] == 'Darwin':
    DRIVE_EXE = os.path.join(this_dir, 'bin/_gshell_drive-osx-x64')
else:
    sys.stderr.write('Not supported os\n')
    sys.exit(1)



@click.group()
@click.version_option(__version__, '-V', '--version')
def cli():
    init()
    pass


def init():
    if not os.path.exists(os.path.expanduser('~/.gdrive/token_v2.json')):
        subprocess.call('{} list --query "trashed = false"'
                        .format(DRIVE_EXE), shell=True)
    if not os.path.exists(CONFIG_FILE):
        init_config()


def _get_home_id():
    cmd = '{exe} list'.format(exe=DRIVE_EXE)
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Id', header).start()
    end = re.search('Name', header).start()
    parent_id = lines[1][start:end].strip()
    while parent_id is not None:
        child_id = parent_id
        parent_id = get_parent_id(child_id)
    return child_id


def init_config():
    home_id = _get_home_id()
    config = {'home_id': home_id, 'id': home_id}
    yaml.dump(config, open(CONFIG_FILE, 'w'), default_flow_style=False)
    return config


def getcwd():
    if os.path.exists(CONFIG_FILE):
        return yaml.load(open(CONFIG_FILE))
    return init_config()


def get_name_by_id(id):
    cmd = '{exe} info {id}'.format(exe=DRIVE_EXE, id=id)
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        if l.startswith('Name: '):
            return l.split()[-1]


@cli.command(name='upload', help='upload file')
@click.argument('filenames', required=True,
                type=click.Path(exists=True), nargs=-1)
@click.option('-r', '--recursive', is_flag=True,
              help='remove files recursively')
def cmd_upload(filenames, recursive):
    cwd = getcwd()
    commands = []
    for fname in filenames:
        cmd = '{exe} upload {file} --parent {pid}'.format(
            exe=DRIVE_EXE, file=fname, pid=cwd['id'])
        if recursive:
            cmd += ' --recursive'
        subprocess.call(cmd, shell=True)


@cli.command(name='download', help='download file')
@click.argument('filename', required=True)
def cmd_download(filename):
    id = get_id_by_name(filename)
    cmd = '{exe} download --id {id}'.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='rm', help='remove file')
@click.argument('filename', required=True)
@click.option('-r', '--recursive', is_flag=True,
              help='remove files recursively')
def cmd_rm(filename, recursive):
    id = get_id_by_name(filename)
    cmd = '{exe} delete'
    if recursive:
        cmd += ' --recursive'
    cmd += ' {id}'
    cmd = cmd.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='ll', help='list files in detail')
def cmd_ll():
    cwd = getcwd()
    cmd = '''{exe} list --query "trashed = false and '{pid}' in parents"'''\
        .format(exe=DRIVE_EXE, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='ls', help='list files')
@click.argument('path', required=False)
def cmd_ls(path):
    if path is None:
        cwd = getcwd()
        id = cwd['id']
    else:
        id = get_id_by_path(path)
    cmd = '''{exe} list --query "trashed = false and '{pid}' in parents"'''\
        .format(exe=DRIVE_EXE, pid=id)
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Name', header).start()
    end = re.search('Type', header).start()
    path = '' if path is None else path
    print('\n'.join(os.path.join(path, l[start:end].strip())
                    for l in stdout.splitlines()[1:]))


@cli.command(name='mkdir', help='make directory')
@click.argument('dirname', required=True)
def cmd_mkdir(dirname):
    cwd = getcwd()
    cmd = '{exe} folder --title {name} --parent {pid}'.format(
        exe=DRIVE_EXE, name=dirname, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='pwd', help='print current working directory')
@click.option('--show-id', default=False, is_flag=True,
              help='show current directory id')
def cmd_pwd(show_id):
    cwd = getcwd()
    id = cwd['id']
    if show_id:
        print(id)
        return
    pwd = deque()
    while id is not None:
        if id == cwd['home_id']:
            pwd.appendleft('~')
            break
        pwd.appendleft(get_name_by_id(id))
        id = get_parent_id(id)
    print(os.path.join(*pwd))


def get_id_by_path(path):
    cwd = getcwd()
    for d in path.split('/'):
        if not d:
            continue
        if d == '..':
            id = get_parent_id(cwd['id']) or cwd['id']
        else:
            id = get_id_by_name(d, cwd=cwd)
            if id is None:
                sys.stderr.write('directory {name} does not exist\n'
                                .format(name=d))
                sys.exit(1)
        cwd['id'] = id
    return cwd['id']



def get_id_by_name(name, cwd=None):
    cwd = cwd or getcwd()
    cmd = '''{exe} list --query "trashed = false and '{pid}' in parents"'''\
        .format(exe=DRIVE_EXE, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Name', header).start()
    end = re.search('Type', header).start()
    for l in stdout.splitlines()[1:]:
        id, title = l[:start].strip(), l[start:end].strip()
        if len(name) > 40:
            name = name[:19] + '...' + name[-18:]
        if name == title:
            return id


def get_parent_id(id):
    cmd = '{exe} info {id}'.format(exe=DRIVE_EXE, id=id)
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    for l in stdout.splitlines():
        if l.startswith('Parents: '):
            return l.split()[-1]


@cli.command(name='cd', help='change directory')
@click.argument('dirname', required=False)
@click.option('--with-id', default=False, is_flag=True,
              help='change directory with folder id')
def cmd_cd(dirname, with_id):
    cwd = getcwd()
    if with_id:
        id = dirname
        dirname = get_name_by_id(id=id)
        cwd['id'] = id
    elif dirname is None:
        cwd['id'] = cwd['home_id']
    else:
        cwd['id'] = get_id_by_path(dirname)
    yaml.dump(cwd, open(CONFIG_FILE, 'w'), default_flow_style=False)


@cli.command(name='open', help='open current site on browser')
def cmd_open():
    cwd = getcwd()
    if platform.uname()[0] == 'Linux':
        open_exe = 'gnome-open'
    elif platform.uname()[0] == 'Darwin':
        open_exe = 'open'
    else:
        sys.stderr.write('Not supported os\n')
        sys.exit(1)
    cmd = "{exe} 'https://drive.google.com/drive/u/1/folders/{id}'"\
        .format(exe=open_exe, id=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='share', help='share file')
@click.argument('filename', required=True)
def cmd_share(filename):
    id = get_id_by_name(name=filename)
    cmd = '{exe} share {id}'.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='info', help='show file information')
@click.argument('filename', required=True)
@click.option('--with-id', default=False, is_flag=True,
              help='change directory with folder id')
def cmd_info(filename, with_id):
    if with_id:
        id = filename
    else:
        id = get_id_by_name(name=filename)
    cmd = '{exe} info {id}'.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


def main():
    cli()


if __name__ == '__main__':
    main()
