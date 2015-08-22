# bgmcli
##Unofficial APIs and a simple CLI for Bangumi.tv in Python

####Note: It only supports Python 2.7, and is only tested with OSX 10.10 and Python 2.7.10

Simple examples for using the APIs. Note it currently only works with anime collections

```python
import codecs
from bgmcli.api import BangumiSession

# to mark subject id 253 as watched, rate it 8, and add a few tags
with BangumiSession('xxxxx@gmail.com', 'password') as session:
    coll = session.get_sub_collection('253')
    coll.c_status = 2
    coll.rating = 8
    coll.tags = ['SUNRISE', 'TV']
    coll.sync_collection()

# to export all anime you are watching and your progress
with BangumiSession('xxxxx@gmail.com', 'password') as session:
    watching = session.get_dummy_collections('anime', 3)
    serialized = [coll.to_regular_collection().to_json() for coll in watching]
with codecs.open('watching.txt', 'w', encoding='utf8') as f:
    f.write('\n'.join(serialized))
```

For the CLI, simply add a config file "~/.bgmcli-config" for login
info as documented in CLI, and type "bgmcli" from terminal.

It currently only supports listing and manipulating anime in the staus of "watching" and their associated episodes,
but there are features like auto-completion for titles and it supports using pinyin of the Chinese title.
