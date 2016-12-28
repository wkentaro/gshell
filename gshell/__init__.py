#!/usr/bin/env python

from __future__ import print_function

import os
import os.path as osp
import pkg_resources
import platform
import re
import subprocess
import sys

import click
from termcolor import cprint
import yaml


__author__ = 'Kentaro Wada <www.kentaro.wada@gmail.com>'
__version__ = pkg_resources.get_distribution('gshell').version


this_dir = osp.dirname(osp.abspath(osp.realpath(__file__)))
CONFIG_FILE = osp.expanduser('~/.gshell')
if platform.uname()[0] == 'Linux':
    DRIVE_EXE = osp.join(this_dir, 'bin/_gshell_drive-linux-x64')
elif platform.uname()[0] == 'Darwin':
    DRIVE_EXE = osp.join(this_dir, 'bin/_gshell_drive-osx-x64')
else:
    sys.stderr.write('Not supported os\n')
    sys.exit(1)


@click.group()
@click.version_option(__version__, '-V', '--version')
def cli():
    pass


def init(name='system'):
    home_dir = osp.expanduser('~')
    if name == 'system':
        config_dir = osp.join(home_dir, '.gdrive')
    else:
        config_dir = osp.join(home_dir, '.gshell_configs', name)

    if not osp.exists(osp.join(config_dir, 'token_v2.json')):
        cprint('Initializing {name} ({config})'
               .format(name=name, config=config_dir), color='green')
        cmd = '{exe} --config {config} about'.format(
            exe=DRIVE_EXE, config=config_dir)
        subprocess.call(cmd, shell=True)
    if not osp.exists(CONFIG_FILE):
        init_config()

    return config_dir


def _get_current_config_dir():
    default_config_dir = osp.expanduser('~/.gdrive')
    if osp.exists(CONFIG_FILE):
        config = yaml.load(open(CONFIG_FILE))
        name = config.get('name', 'system')
    else:
        name = 'system'
    if name == 'system':
        config_dir = default_config_dir
    else:
        config_dir = osp.join(osp.expanduser('~/.gshell_configs'), name)
    if not osp.exists(osp.join(config_dir, 'token_v2.json')):
        config_dir = init(name)
    return config_dir


def _get_home_id():
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} list'.format(
        exe=DRIVE_EXE, config=config_dir)
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


def init_config(name='system'):
    home_id = _get_home_id()
    config = {'home_id': home_id, 'id': home_id, 'name': name}
    yaml.dump(config, open(CONFIG_FILE, 'w'), default_flow_style=False)
    return config


def getcwd():
    if osp.exists(CONFIG_FILE):
        return yaml.load(open(CONFIG_FILE))
    return init_config()


def get_name_by_id(id):
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} info {id}'.format(
        exe=DRIVE_EXE, config=config_dir, id=id)
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        if l.startswith('Name: '):
            return l.split()[-1]


@cli.command(name='init', help='initialize gshell')
@click.argument('name', default='system', required=False)
def cmd_init(name):
    config_dir = init(name)
    print('{name}: {config}'.format(name=name, config=config_dir))


@cli.command(name='switch', help='switch user')
@click.argument('name', required=False)
def cmd_switch(name):
    config_list_dir = osp.expanduser('~/.gshell_configs')
    if not osp.exists(config_list_dir):
        os.mkdir(config_list_dir)
    if name is None:
        config = yaml.load(open(CONFIG_FILE, 'r'))
        current_name = config.get('name', 'system')
        config_list = {name: osp.join(config_list_dir, name)
                       for name in os.listdir(config_list_dir)}
        config_list['system'] = osp.expanduser('~/.gdrive')
        for name, config_dir in config_list.items():
            flag = '*' if current_name == name else ' '
            print('{flag} {name} ({config})'
                  .format(flag=flag, name=name, config=config_dir))
    else:
        config_dir = osp.join(config_list_dir, name)
        if name == 'system' or osp.exists(config_dir):
            config = yaml.load(open(CONFIG_FILE, 'r'))
            config['name'] = name
            yaml.dump(config, open(CONFIG_FILE, 'w'), default_flow_style=True)
            init_config(name)
            cprint('Switched to {name} ({config}).'
                   .format(name=name, config=config_dir),
                   color='green')
        else:
            cprint('Config for {name} ({config}) does not exist.'
                   .format(name=name, config=config_dir),
                   color='red')


@cli.command(name='about', help='show account status')
def cmd_about():
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} about'.format(
        exe=DRIVE_EXE, config=config_dir)
    subprocess.call(cmd, shell=True)


@cli.command(name='upload', help='upload file')
@click.argument('filenames', required=True,
                type=click.Path(exists=True), nargs=-1)
@click.option('-r', '--recursive', is_flag=True,
              help='upload files recursively')
def cmd_upload(filenames, recursive):
    config_dir = _get_current_config_dir()
    cwd = getcwd()
    for fname in filenames:
        cmd = '{exe} --config {config} upload {file} --parent {pid}'.format(
            exe=DRIVE_EXE, config=config_dir, file=fname, pid=cwd['id'])
        if recursive:
            cmd += ' --recursive'
        subprocess.call(cmd, shell=True)


@cli.command(name='download', help='download file')
@click.argument('filename', required=True)
@click.option('-r', '--recursive', is_flag=True,
              help='download directory recursively')
@click.option('--with-id', default=False, is_flag=True,
              help='change directory with folder id')
def cmd_download(filename, recursive, with_id):
    if with_id:
        id = filename
    else:
        id = get_id_by_name(filename)
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} download {id}'.format(
        exe=DRIVE_EXE, config=config_dir, id=id)
    if recursive:
        cmd += ' --recursive'
    subprocess.call(cmd, shell=True)


@cli.command(name='rm', help='remove file')
@click.argument('filename', required=True)
@click.option('-r', '--recursive', is_flag=True,
              help='remove files recursively')
def cmd_rm(filename, recursive):
    config_dir = _get_current_config_dir()
    id = get_id_by_name(filename)
    cmd = '{exe} --config {config} delete'.format(
        exe=DRIVE_EXE, config=config_dir)
    if recursive:
        cmd += ' --recursive'
    cmd += ' {id}'.format(id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='ll', help='list files in detail')
def cmd_ll():
    config_dir = _get_current_config_dir()
    cwd = getcwd()
    cmd = '{exe} --config {config} list'
    cmd += ''' --query "trashed = false and '{pid}' in parents"'''
    cmd += ' --max 100 --name-width 0'
    cmd = cmd.format(exe=DRIVE_EXE, config=config_dir, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='ls', help='list files')
@click.argument('path', required=False)
def cmd_ls(path):
    if path is None:
        cwd = getcwd()
        id = cwd['id']
    else:
        id = get_id_by_path(path)
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} list'
    cmd += ''' --query "trashed = false and '{pid}' in parents"'''
    cmd += ' --max 100 --name-width 0'
    cmd = cmd.format(exe=DRIVE_EXE, config=config_dir, pid=id)
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Name', header).start()
    end = re.search('Type', header).start()
    path = '' if path is None else path
    print('\n'.join(osp.join(path, l[start:end].strip())
                    for l in stdout.splitlines()[1:]))


@cli.command(name='mkdir', help='make directory')
@click.argument('dirname', required=True)
def cmd_mkdir(dirname):
    cwd = getcwd()
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} mkdir {name} --parent {pid}'.format(
        exe=DRIVE_EXE, config=config_dir, name=dirname, pid=cwd['id'])
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
    if cwd['id'] == cwd['home_id']:
        print('~')
        return
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} info {id}'.format(
        exe=DRIVE_EXE, config=config_dir, id=id)
    stdout = subprocess.check_output(cmd, shell=True).strip()
    for line in stdout.splitlines():
        if not line.startswith('Path: '):
            continue
        path = line[len('Path: '):]
        pwd = osp.join('~', path)
        print(pwd)
        return


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
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} list'
    cmd += ''' --query "trashed = false and '{pid}' in parents"'''
    cmd += ' --max 100 --name-width 0'
    cmd = cmd.format(exe=DRIVE_EXE, config=config_dir, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True).decode('utf-8')
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Name', header).start()
    end = re.search('Type', header).start()
    for l in stdout.splitlines()[1:]:
        id, title = l[:start].strip(), l[start:end].strip()
        if name == title:
            return id


def get_parent_id(id):
    config = _get_current_config_dir()
    cmd = '{exe} --config {config} info {id}'.format(
        exe=DRIVE_EXE, config=config, id=id)
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
    config_dir = _get_current_config_dir()
    id = get_id_by_name(name=filename)
    cmd = '{exe} --config {config} share {id}'.format(
        exe=DRIVE_EXE, config=config_dir, id=id)
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
    config_dir = _get_current_config_dir()
    cmd = '{exe} --config {config} info {id}'.format(
        exe=DRIVE_EXE, config=config_dir, id=id)
    subprocess.call(cmd, shell=True)


def main():
    cli()


if __name__ == '__main__':
    main()
