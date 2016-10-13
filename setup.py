""" Setup for python-verisure """

from setuptools import setup

setup(
    name='vsure',
    version='0.11.1',
    description='Read and change status of verisure devices through mypages.',
    long_description='A module for reading and changing status of ' +
    'verisure devices through mypages. Compatible ' +
    'with both Python2.7 and Python3.',
    url='http://github.com/persandstrom/python-verisure',
    author='Per Sandstrom',
    author_email='per.j.sandstrom@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Home Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    keywords='home automation verisure',
    install_requires=['requests>=2.9.1'],
    packages=['verisure', 'verisure.devices'],
    zip_safe=True,
    entry_points={
        'console_scripts': [
            'vsure=verisure.__main__:main',
        ]
    })
