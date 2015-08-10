from setuptools import setup

setup(
    name='python-verisure',
    version='0.1',
    description='read and change status of verisure devices through mypages.',
    url='http://github.com/persandstrom/python-verisure',
    author='Per Sandström',
    license='MIT',
    install_requires=['requests>=2.0'],
    packages=['verisure'],
    zip_safe=True)
