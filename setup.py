# coding: utf-8

from __future__ import absolute_import
import os
from setuptools import setup, find_packages


def _read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


setup(
    name='m3-ssosp',
    url='https://bitbucket.org/barsgroup/ssosp',
    license='MIT',
    author='BARS Group',
    author_email='bars@bars-open.ru',
    package_dir={'': 'src'},
    packages=find_packages('src'),
    description=_read('DESCRIPTION.md'),
    install_requires=(
        'six>=1.10.0',
        'lxml>=3.0',
        'rsa>=3.1.2',
        'django>=1.3',
        'm3-django-compat>=1.2.1',
    ),
    long_description=_read('README.md'),
    include_package_data=True,
    classifiers=(
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'License :: OSI Approved :: MIT License',
        'Development Status :: 5 - Production/Stable',
    ),
    dependency_links=('http://pypi.bars-open.ru/simple/m3-builder',),
    setup_requires=('m3-builder>=1.0.1',),
    set_build_info=os.path.dirname(__file__),
)
