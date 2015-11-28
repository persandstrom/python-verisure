""" Setup for python-verisure """

from setuptools import setup

setup(
    name='python-verisure',
    version='0.3.2',
    description='read and change status of verisure devices through mypages.',
    long_description=
    'A module for reading and changing status of ' +
    'verisure devices through mypages. Compatible ' +
    'with both Python2.7 and Python3.',
    url='http://github.com/persandstrom/python-verisure',
    author='Per Sandstrom',
    license='MIT',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Home Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        ],
    keywords='home automation verisure',
    install_requires=['requests>=2.0'],
    packages=['verisure', 'verisure.devices'],
    zip_safe=True)
