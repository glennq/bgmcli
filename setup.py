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
        'prompt-toolkit==0.47',
        'xpinyin==0.5.3',
    ],
    entry_points={
        'console_scripts': [
            'bgmcli = bgmcli.cli.interface:run',
        ]
    },
)