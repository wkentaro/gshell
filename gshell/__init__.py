#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import subprocess
import yaml

import click


__author__ = 'Kentaro Wada <www.kentaro.wada@gmail.com>'
__version__ = '1.0.2'


this_dir = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
CONFIG_FILE = os.path.expanduser('~/.gshell')
DRIVE_EXE = '_gshell_drive'


@click.group()
def cli():
    pass


def init():
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
    cwd = getcwd()
    cmd = '{exe} upload --file {file} --parent {pid}'.format(exe=DRIVE_EXE, file=filename, pid=cwd['id'])
    subprocess.call(cmd, shell=True)


@cli.command(name='ll')
def ls():
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents" --noheader'''.format(exe=DRIVE_EXE, pid=cwd['id'])
    subprocess.call(cmd, shell=True)

@cli.command(name='ls')
def ls():
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents"'''.format(exe=DRIVE_EXE, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True)
    lines = stdout.splitlines()
    header = lines[0]
    start = re.search('Title', header).start()
    end = re.search('Size', header).start()
    print('\n'.join([l[start:end] for l in stdout.splitlines()[1:]]))


@cli.command(name='mkdir')
@click.argument('dirname', required=True)
def mkdir(dirname):
    cmd = '{exe} folder --title {name} --parent {pid}'.format(exe=DRIVE_EXE, name=dirname, pid=MYDRIVE_ID)
    subprocess.call(cmd, shell=True)


@cli.command(name='pwd')
def pwd():
    print(getcwd()['name'])


# def _get_filenames():
#     cwd = getcwd()
#     cmd = '''{exe} list --query " '{pid}' in parents" --noheader'''.format(exe=DRIVE_EXE, pid=cwd['id'])
#     stdout = subprocess.check_output(cmd, shell=True)
#     for l in stdout.splitlines():
#         id = l.split()[0]
#         yield get_name_by_id(id=id)


def get_id_by_name(name):
    cwd = getcwd()
    cmd = '''{exe} list --query " '{pid}' in parents" --noheader'''.format(exe=DRIVE_EXE, pid=cwd['id'])
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        id, title = l.split('   ')[:2]
        if len(name) > 40:
            name = name[:19] + '...' + name[-18:]
        if name == title:
            return id


def get_parent_id(id):
    cmd = '{exe} info --id {id}'.format(exe=DRIVE_EXE, id=id)
    stdout = subprocess.check_output(cmd, shell=True)
    for l in stdout.splitlines():
        if l.startswith('Parents: '):
            return l.split()[-1]


@cli.command(name='cd')
@click.argument('dirname', required=False)
def cd(dirname):
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
        cwd['id'] = id
        cwd['name'] = get_name_by_id(id=id)
    yaml.dump(cwd, open(CONFIG_FILE, 'w'))


if __name__ == '__main__':
    cli()
