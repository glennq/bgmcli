from .element import BangumiEpisode, BangumiSubject

def pickle_episode(episode):
    kwargs = episode.__dict__
    kwargs['version'] = (0, 0, 1)
    return unpickle_episode, (kwargs,)


def unpickle_episode(kwargs):
    version = kwargs.pop('version', (0, 0, 1))
    if version == (0, 0, 1):
        kwargs.pop('_subject')
    kwargs = {key[1:]: value for key, value in kwargs.items()}
    return BangumiEpisode(**kwargs)
        





