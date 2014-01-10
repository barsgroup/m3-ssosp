#coding: utf-8
import os
from setuptools import setup, find_packages

def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__),
            fname)).read()
    except IOError:
        return ''

setup(name='ssosp',
      version='1.1.0',
      url='https://bitbucket.org/barsgroup/ssosp',
      license='MIT License',
      author='BARS Group',
      author_email='kirov@bars-open.ru',
      package_dir={'': 'src'},
      packages=find_packages('src'),
      description=u'Single Sign-On Service Provider',
      install_requires=read('REQUIREMENTS'),
      include_package_data=True,
      classifiers=[
        'Intended Audience :: Developers',
        'Environment :: Web Environment',
        'Natural Language :: Russian',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
      ],
      )
