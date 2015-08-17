from setuptools import setup, find_packages

setup(
    name='bgmcli',
    author='Jiyuan Qian',
    version='0.0.1',
    description='Unofficial API and CLI for Bangumi.tv',
    packages=find_packages('.', exclude="tests"),
    install_requires=[
        'requests',
        'beautifulsoup4',
    ],
)
