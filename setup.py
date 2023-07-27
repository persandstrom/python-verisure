""" Setup for python-verisure """

from setuptools import setup

setup(
    name='vsure',
    version='2.6.3',
    description='Read and change status of verisure devices through mypages.',
    long_description='A python3 module for reading and changing status of '
    + 'verisure devices through mypages.',
    url='http://github.com/persandstrom/python-verisure',
    author='Per Sandstrom',
    author_email='per.j.sandstrom@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Home Automation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    keywords='home automation verisure',
    setup_requires=['wheel'],
    install_requires=[
        'requests>=2.25.1',
        'click>=8.0.0a1'],
    packages=['verisure'],
    zip_safe=True,
    entry_points='''
        [console_scripts]
        vsure=verisure.__main__:cli
    '''
    )
