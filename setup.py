from setuptools import setup, find_packages

setup(
    name='bgmcli',
    author='Jiyuan Qian',
    version='0.1.0',
    description='Unofficial API and CLI for Bangumi.tv',
    packages=find_packages('.', exclude="tests"),
    install_requires=[
        'requests==2.7.0',
        'beautifulsoup4==4.3.2',
        'prompt-toolkit==0.47',   # for CLI only
        'xpinyin==0.5.3',   # for CLI only
    ],
    entry_points={
        'console_scripts': [
            'bgmcli = bgmcli.cli.interface:run',
        ]
    },
)