# bgmcli
##Unofficial APIs and a simple CLI for Bangumi.tv in Python

Note:

It only supports Python 2.7, and is only tested with OSX 10.10 and
Python 2.7.10

Simple examples for using the APIs. Note it currently only works with anime collections

```
from bgmcli.api import BangumiSession

# to mark subject id 253 as watched, rate it 8, and add a few tags
with BangumiSession('xxxxx@gmail.com', 'xxxxxx') as session:
    coll = session.get_sub_collection('253')
    coll.c_status = 3
    coll.rating = 
    coll.tags = ['SUNRISE', 'TV']
    coll.sync_collection()
```

For the CLI, simply add a config file "~/.bgmcli-config" for login info as documented in CLI, and type "bgmcli" from terminal.
It currently only supports listing and manipulating anime in the staus of "watching" and their associated episodes,
but there are features like auto-completion for titles and it supports using pinyin of the Chinese title.
