#!/usr/bin/env python

from __future__ import print_function

import os
import platform
import subprocess
import sys

from setuptools import find_packages
from setuptools import setup


version = '5.5.3'


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
if sys.argv[-1] == 'release':
    for cmd in [
        'git tag %s' % version,
        'git push origin master --tags',
        'python setup.py sdist',
        'twine upload dist/gshell-%s.tar.gz' % version,
    ]:
        subprocess.check_call(cmd, shell=True)
    sys.exit(0)

setup(
    name='gshell',
    version=version,
    packages=find_packages(),
    package_data={'gshell': ['bin/_gshell_drive-*']},
    description='Tool to handle google drive as shell',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
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
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
    entry_points={'console_scripts': ['gshell=gshell:main']},
    data_files=get_data_files(),
)
