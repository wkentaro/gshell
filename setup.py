#!/usr/bin/env python

from __future__ import print_function
import os
import platform
import subprocess
import sys

from setuptools import find_packages
from setuptools import setup


version = '5.0.2'


def get_data_files():

    def get_completion_install_location(shell):
        uname = platform.uname()[0]
        is_root = (os.geteuid() == 0)
        prefix = ''
        if is_root:
            # this is system install
            if uname == 'Linux' and shell == 'bash':
                prefix = '/'
            elif uname == 'Linux' and shell == 'zsh':
                prefix = '/usr/local'
            elif uname == 'Darwin' and shell == 'bash':
                prefix = '/'
            elif uname == 'Darwin' and shell == 'zsh':
                prefix = '/usr'
        if shell == 'bash':
            location = os.path.join(prefix, 'etc/bash_completion.d')
        elif shell == 'zsh':
            location = os.path.join(prefix, 'share/zsh/site-functions')
        else:
            raise ValueError('unsupported shell: {0}'.format(shell))
        return location

    loc = {'bash': get_completion_install_location(shell='bash'),
           'zsh': get_completion_install_location(shell='zsh')}
    files = dict(bash=['completion/gshell-completion.bash'],
                 zsh=['completion/gshell-completion.bash',
                      'completion/_gshell'])
    data_files = []
    data_files.append((loc['bash'], files['bash']))
    data_files.append((loc['zsh'], files['zsh']))
    return data_files


# publish helper
if sys.argv[-1] == 'publish':
    for cmd in [
            'git tag {}'.format(version),
            'git push origin master --tag',
            'python setup.py sdist upload -r pypi',
            ]:
        subprocess.check_call(cmd, shell=True)
    sys.exit(0)

setup(
    name='gshell',
    version=version,
    packages=find_packages(),
    package_data={'gshell': ['bin/_gshell_drive-*']},
    description='Tool to handle google drive as shell',
    long_description=open('README.rst').read(),
    author='Kentaro Wada',
    author_email='www.kentaro.wada@gmail.com',
    url='http://github.com/wkentaro/gshell',
    install_requires=open('requirements.txt').readlines(),
    license='MIT',
    keywords='utility',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Topic :: Internet :: WWW/HTTP',
        ],
    entry_points={'console_scripts': ['gshell=gshell:main']},
    data_files=get_data_files(),
)
