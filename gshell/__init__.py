#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys
import yaml

import click


__author__ = 'Kentaro Wada <www.kentaro.wada@gmail.com>'
__version__ = '1.0.8'


this_dir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
CONFIG_FILE = os.path.expanduser('~/.gshell')
DRIVE_EXE = '_gshell_drive'


@click.group()
def cli():
    pass


def init():
    if not os.path.exists(os.path.expanduser('~/.gdrive')):
        subprocess.call(DRIVE_EXE, shell=True)


def get_name_by_id(id):
    cmd = '{exe} info --id {id}'.format(exe=DRIVE_EXE, id=id)
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        if l.startswith('Title: '):
            return l.split()[-1]


def getcwd():
    if os.path.exists(CONFIG_FILE):
        return yaml.load(open(CONFIG_FILE))
    home_id = raw_input('Please specify home directory id: ')
    name = get_name_by_id(home_id)
    config = {'home_id': home_id, 'home_name': name,
              'id': home_id, 'name': name}
    yaml.dump(config, open(CONFIG_FILE, 'w'))
    return config


@cli.command(name='upload')
@click.argument('filename', required=True, type=click.Path(exists=True))
def upload(filename):
    init()
    cwd = getcwd()
    cmd = '{exe} upload --file {file} --parent {pid}'.format(
        exe=DRIVE_EXE, file=filename, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='download')
@click.argument('filename', required=True)
def download(filename):
    init()
    id = get_id_by_name(filename)
    cmd = '{exe} download --id {id}'.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='rm')
@click.argument('filename', required=True)
def rm(filename):
    init()
    id = get_id_by_name(filename)
    cmd = '{exe} delete --id {id}'.format(exe=DRIVE_EXE, id=id)
    subprocess.call(cmd, shell=True)


@cli.command(name='ll')
def ll():
    init()
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents" --noheader'''.format(
        exe=DRIVE_EXE, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='ls')
def ls():
    init()
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents"'''.format(
        exe=DRIVE_EXE, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True)
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Title', header).start()
    end = re.search('Size', header).start()
    print('\n'.join([l[start:end].strip() for l in stdout.splitlines()[1:]]))


@cli.command(name='mkdir')
@click.argument('dirname', required=True)
def mkdir(dirname):
    init()
    cwd = getcwd()
    cmd = '{exe} folder --title {name} --parent {pid}'.format(
        exe=DRIVE_EXE, name=dirname, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='pwd')
def pwd():
    init()
    print(getcwd()['name'])


def get_id_by_name(name):
    init()
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents"'''.format(
        exe=DRIVE_EXE, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True)
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Title', header).start()
    end = re.search('Size', header).start()
    for l in stdout.splitlines()[1:]:
        id, title = l[:start].strip(), l[start:end].strip()
        if len(name) > 40:
            name = name[:19] + '...' + name[-18:]
        if name == title:
            return id


def get_parent_id(id):
    init()
    cmd = '{exe} info --id {id}'.format(exe=DRIVE_EXE, id=id)
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        if l.startswith('Parents: '):
            return l.split()[-1]


@cli.command(name='cd')
@click.argument('dirname', required=False)
def cd(dirname):
    init()
    cwd = getcwd()
    if dirname is None:
        cwd['id'] = cwd['home_id']
        cwd['name'] = cwd['home_name']
    elif dirname == '..':
        id = get_parent_id(cwd['id'])
        cwd['id'] = id
        cwd['name'] = get_name_by_id(id=id)
    else:
        id = get_id_by_name(dirname)
        if id is None:
            sys.stderr.write('directory {name} does not exist\n'
                             .format(name=dirname))
            sys.exit(1)
        cwd['id'] = id
        cwd['name'] = get_name_by_id(id=id)
    yaml.dump(cwd, open(CONFIG_FILE, 'w'))


if __name__ == '__main__':
    cli()
