# -*- coding: utf-8 -*-
"""Defines collection classes
"""
import re
import weakref
import json
from functools import wraps
import pkg_resources
from bs4 import BeautifulSoup
from .element import BangumiEpisode, BangumiAnime, BangumiSubjectFactory
from .utils import get_user_id_from_soup, get_checked_values, to_unicode,\
    get_ep_colls_up_to_this, get_subject_type_from_soup,\
    get_n_watched_eps_from_soup
from .base import BangumiBase
from _pyio import __metaclass__



CUR_VERSION = pkg_resources.require("bgmcli")[0].version


def require_session(method):
    """Decorator function that raises AttributeError if session is not set"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self._session:
            raise AttributeError("session not set while sync is required")
        else:
            return method(self, *args, **kwargs)
    return wrapper


class BangumiCollection(BangumiBase):
    """Mixin for collection behaviors"""
    
    @property
    def session(self):
        """BangumiSession: session associated for sync
        
        if it's a BangumiAnimeCollection, setter will set sessions for
        all episode collections for this subject as well
        """
        return self._session
    
    @session.setter
    def session(self, session):
        self._session = session
        if isinstance(self, BangumiAnimeCollection) and self.ep_collections:
            for ep_c in self.ep_collections:
                ep_c._session = session
    
    @require_session
    def sync_collection(self):
        """Update Bangumi with current collection data. n_watched_eps is not
        sync'ed for BangumiAnimeCollection
        
        Returns:
            bool: True if successful
            
        Raises:
            AttributeError: if session is not set
        """
        return self._session.set_collection(self)

    @require_session
    def remove_with_sync(self):
        """Remove this collection on Bangumi and clear c_status locally
        
        Returns:
            bool: True if successful
            
        Raises:
            AttributeError: if session is not set
        """
        return self._session.remove_collection(self)
    
    def __eq__(self, other):
        """Does not compare BangumiCollection.session,
        BangumiAnimeCollection.ep_collections,
        and BangumiEpisodeCollection.sub_collection
        """
        if not isinstance(other, self.__class__):
            return False
        else:
            for key, value in self.__dict__.items():
                if key in ['_session', '_ep_collections', '_sub_collection']:
                    continue
                if value != getattr(other, key):
                    return False
            return True

    def __ne__(self, other):
        return not self.__eq__(other)


class SubjectCollectionMeta(type):
    """Metaclass for BangumiSubjectCollection. Helps to register subclasses in 
    BangumiSubjectIndex
    """
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        cls = type.__new__(meta, name, bases, class_dict) 
        (BangumiSubjectCollectionFactory.sub_type_subclass_map
         .update({class_dict['_SUB_TYPE']: cls}))
        return cls
    
    
class BangumiSubjectCollectionFactory(BangumiSubjectFactory):
    """A factory class that identifies which subclass of
    BangumiSubjectCollection need to be instantiated
    
    Attributes:
        sub_type_subclass_map (dict): a mapping from subject type to the
            subclass name that defines this kind of subject collection
    """
    
    sub_type_subclass_map = {}
    
    @classmethod
    def from_html_with_subject(cls, subject, sub_html, ep_html):
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup_with_subject(subject, sub_soup, ep_soup)
    
    @classmethod
    def from_soup_with_subject(cls, subject, sub_soup, ep_soup):
        sub_type = get_subject_type_from_soup(sub_soup)
        if sub_type not in cls.sub_type_subclass_map:
            raise NotImplementedError
        subclass = cls.sub_type_subclass_map[sub_type]
        return subclass.from_soup_with_subject(subject, sub_soup, ep_soup)


class BangumiSubjectCollection(BangumiCollection):
    
    """Class representing a general subject collection.

    Note: 
        The constructor is NOT supposed to be called directly by client code,
        Please use class methods in this class and other methods provided in
        BangumiSession to create instances of BangumiAnimeCollection
        
    Args:
        subject (BangumiSubject): subject belonging to the collection
        c_status (int): status of the collection
        rating (int): rating given to the subject collection
        tags (list[unicode]): tags added to this subject collection
        comment (unicode): comment to this subject collection
    """
    
    _VALID_C_STATUS = tuple(range(1, 6))
    __metaclass__ = SubjectCollectionMeta
    _SUB_TYPE = None
    
    def __init__(self, subject, c_status=None, rating=None, tags=None,
                 comment=None):
        self._subject = subject
        self._c_status = c_status
        self._rating = rating
        self._tags = tags if tags else []
        self._comment = comment if comment else u""
        self._session = None
        
    @classmethod
    def from_html(cls, sub_html, ep_html):
        """Create subject collection object from html
        
        Args:
            sub_html (unicode): html for the subject's main page
            ep_html (unicode): html for the subject's episodes page
            
        Returns:
            BangumiSubjectCollection: subject collection with provided data
        """
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)

    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        """Create subject collection object from parsed html
        
        Args:
            sub_soup (BeautifulSoup): parsed html for subject main page
            ep_soup (BeautifulSoup): parsed html for the episodes page
            
        Returns:
            BangumiSubjectCollection: subject collection with provided data
        """
        subject = BangumiSubjectFactory.from_soup(sub_soup, ep_soup)
        return cls.from_soup_with_subject(subject, sub_soup, ep_soup)

    @classmethod
    def from_html_with_subject(cls, subject, sub_html, ep_html):
        """Create BangumiAnimeCollection object from html with provided
        subject
        
        Args:
            subject (BangumiSubject): subject belonging to the collection
            sub_html (unicode): html for the subject main page
            ep_html (unicode): html for the subject's episodes page
            
        Returns:
            BangumiSubjectCollection: subject collection with provided data
            
        Raises:
            ValueError: if provided html is not after login
        """
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup_with_subject(subject, sub_soup, ep_soup)
    
#     @classmethod
#     def from_soup_with_subject(cls, subject, sub_soup, ep_soup):
#         sub_type = get_subject_type_from_soup(sub_soup)
#         if sub_type == 'anime':
#             return BangumiAnimeCollection.from_soup_with_subject(subject,
#                                                                 sub_soup,
#                                                                 ep_soup)
#         else:
#             raise NotImplementedError
    
    @property
    def subject(self):
        """BangumiAnime: subject that this collection is associated with.
        
        setter will raise TypeError for incorrect type
        """
        return self._subject

    @property
    def c_status(self):
        """int: collection status, 1 stands for want to watch, 2 for watched,
        3 for watching, 4 for temporarily dropped, 5 for dropped
        
        setter raises ValueError for invalid value
        """
        return self._c_status

    @c_status.setter
    def c_status(self, value):
        if value in self._VALID_C_STATUS:
            self._c_status = value
        else:
            raise ValueError("Invalid value provided")

    @property
    def rating(self):
        """int or None: if not None, must be integer >= 1 and <= 10. None for
        no rating.
        
        Setter raises ValueError for invalid values
        """
        return self._rating

    @rating.setter
    def rating(self, value):
        if value is None:
            self._rating = value
        else:
            value = int(value)
            if value >= 1 and value <= 10:
                self._rating = value
            else:
                raise ValueError("Value must be between 1 to 10, got {0}"
                                 .format(value))
    
    @property
    def tags(self):
        """list[unicode]: a list of tags for this collection
        
        setter will check datatype and raise TypeError
        """
        return self._tags
    
    @tags.setter
    def tags(self, value):
        if not isinstance(value, list):
            raise TypeError("tags must be a list of unicode strings, got {0}"
                            .format(type(value)))
        for tag in value:
            tag = to_unicode(tag)
            if not isinstance(tag, unicode):
                raise TypeError("each tag must be unicode strings, got {0}"
                                .format(type(tag)))
        self._tags = value         
        
    @property
    def comment(self):
        """unicode: string of comment for this collection
        
        setter checks type and raises TypeError
        """
        return self._comment
    
    @comment.setter
    def comment(self, value):
        value = to_unicode(value)
        if not isinstance(value, unicode):
            raise TypeError("comment must be a unicode strings, got {0}"
                            .format(type(value)))
        self._comment = value


class BangumiAnimeCollection(BangumiSubjectCollection):
    """Class representing an anime subject collection

    Note: 
        The constructor is NOT supposed to be called directly by client code,
        Please use class methods in this class and other methods provided in
        BangumiSession to create instances of BangumiAnimeCollection
        
    Args:
        subject (BangumiAnime): anime subject belonging to the collection
        c_status (int): status of the collection
        rating (int): rating given to the subject collection
        tags (list[unicode]): tags added to this subject collection
        comment (unicode): comment to this subject collection
        n_watched_eps (int): number of episodes watched
        ep_collections (list[BangumiEpisodeCollection]): episodes collections
            belonging to this subject collection
    """
    
    _SUB_TYPE = 'anime'

    def __init__(self, subject, c_status=None, rating=None, tags=None,
                 comment=None, n_watched_eps=None, ep_collections=None):
        super(BangumiAnimeCollection, self).__init__(subject, c_status,
                                                     rating, tags, comment)
        self._n_watched_eps = n_watched_eps
        self._ep_collections = list(ep_collections) if ep_collections else []
        for ep_coll in self.ep_collections:
            ep_coll.sub_collection = self

    @classmethod
    def from_soup_with_subject(cls, subject, sub_soup, ep_soup):
        """Create BangumiAnimeCollection object from parsed html with
        provided subject
        
        Args:
            subject (BangumiAnime): subject belonging to the collection
            sub_soup (BeautifulSoup): parsed html for the subject main page
            ep_soup (BeautifulSoup): parsed html for the episodes page
            
        Returns:
            BangumiAnimeCollection: subject collection with provided data
            
        Raises:
            ValueError: if provided html is not after login
        """
        try:
            get_user_id_from_soup(sub_soup)
        except TypeError:
            raise ValueError("Please provide subject page html after login!")
        else:
            if sub_soup.find(id='SecTab'):
                return BangumiAnimeCollection(subject)
            collect_form = sub_soup.find(id='collectBoxForm')
            status = int(get_checked_values(
                collect_form.find(class_='collectType'))[0])
            rating_container = get_checked_values(
                collect_form.find(id='interest_rate'))
            rating = int(rating_container[0]) if rating_container else None
            tags = collect_form.find(id='tags')['value'].strip().split(' ')
            comment = collect_form.find(id='comment').text
            n_watched_eps = get_n_watched_eps_from_soup(sub_soup)
            ep_collections = (BangumiEpisodeCollection
                              .ep_colls_for_sub_from_soup(subject, ep_soup))
            return cls(subject, status, rating, tags, comment, n_watched_eps,
                       ep_collections)

    @classmethod
    def from_json(cls, json_text):
        """Convert back from json
        
        Args:
            json_text (unicode): json text to convert from
            
        Returns:
            BangumiAnimeCollection: created from data in json text
        """
        kwargs = json.loads(json_text)
        kwargs.pop('version', (0, 0, 1))
        kwargs = {(key[1:] if key.startswith('_') else key): value
                  for key, value in kwargs.items()}
        kwargs['ep_collections'] = [BangumiEpisodeCollection.from_json(j_text)
                                    for j_text in kwargs['ep_collections']]
        kwargs['subject'] = BangumiAnime.from_json(kwargs['subject'])
        sub_coll = cls(**kwargs)
        sub_coll.subject._eps = [ep_coll.episode for ep_coll
                                 in sub_coll.ep_collections]
        for ep_coll in sub_coll.ep_collections:
            ep_coll.sub_collection = sub_coll
        for ep in sub_coll.subject.eps:
            ep.subject = sub_coll.subject
        return sub_coll
    
    def to_json(self):
        """Convert to json
        
        Returns:
            unicode: converted json text
        """
        kwargs = self.__dict__.copy()
        kwargs['version'] = CUR_VERSION
        kwargs.pop('_session')
        kwargs['_ep_collections'] = [ep_coll.to_json() for ep_coll in
                                     kwargs['_ep_collections']]
        # temporarily drop subject._eps to avoid duplicating information,
        # since _ep_collections already contains data for episodes
        sub, eps = kwargs['_subject'], kwargs['_subject']._eps
        kwargs['_subject']._eps = []
        kwargs['_subject'] = kwargs['_subject'].to_json()
        sub._eps = eps
        return json.dumps(kwargs, ensure_ascii=False)

    @property
    def n_watched_eps(self):
        """int: number of episodes watched. Must be non-negative and less than
        available regular episodes
        
        setter raises ValueError for invalid values
        """
        return self._n_watched_eps
    
    @n_watched_eps.setter
    def n_watched_eps(self, value):
        value = int(value)
        if value < 0 or ((self.subject.n_eps and self.subject.n_eps) and
                         value > len(self.subject.eps)):
            raise ValueError("n_watched_eps must be non-negative and less " + 
                             "than n_eps, got {0}".format(value))
        self._n_watched_eps = value

    @property
    def ep_collections(self):
        """tuple[BangumiEpisodeCollection]: episode collections belonging to
        this subject collection
        
        setter will check type of each entry and raise TypeError if incorrect
        """
        return tuple(self._ep_collections)
    
    @ep_collections.setter
    def ep_collections(self, value):
        value = list(value)
        for ep_coll in value:
            if not isinstance(ep_coll, BangumiEpisodeCollection):
                raise TypeError("Each entry must be BangumiEpisode, got {0}"
                                .format(type(ep_coll)))
        self._ep_collections = value

    @require_session
    def watched_up_to_with_sync(self, ep_info):
        """Set watched episodes up to the one specified, sync immediately
        
        Args:
            ep_info (BangumiEpisodeCollection, str): information needed
                to identify the episode. Can be a episode collection
                contained, episode id, or episode number prepended with
                episode type: eg. 'EP15' or 'SP1'
                
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            AttributeError: if session not set
            TypeError: if ep_info not correct type
        """
        if isinstance(ep_info, BangumiEpisodeCollection):
            if ep_info not in self.ep_collections:
                raise ValueError("Provided BangumiEpisodeCollection not in " +
                                 "this subject collection")
            ep_coll = ep_info
        elif isinstance(ep_info, str):
            ep_coll = self.find_ep_coll(ep_info)
            if not ep_coll:
                raise ValueError("Provided ep_info not in this subject" +
                                 "collection")
        else:
            raise TypeError("ep_info must be BangumiEpisodeCollection or " +
                            "str, got {0}".format(type(ep_info)))

        ep_colls = get_ep_colls_up_to_this(ep_coll)
        return self._session._set_watched_eps_in_sub(ep_colls)
    
    @require_session
    def watched_eps_with_sync(self, ep_colls):
        """Set watched episodes for ep_ids specified, sync immediately
        
        Args:
            ep_colls (list[BangumiEpisodeCollection]): episode collections to
                be marked as watched
                
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            AttributeError: if session not set
            ValueError: if some entry in ep_colls does not belong to this
                collection
        """
        for ep_coll in ep_colls:
            if ep_coll not in self.ep_collections:
                raise ValueError("Every entry in ep_colls must belong to " +
                                 "this collection")
        return self._session._set_watched_eps_in_sub(ep_colls)
        
    def find_ep_coll(self, ep_info):
        """Search for episode collection with ep_info. Result should be unique
        
        Args:
            ep_info (str): information to identify the episode. episode id,
                or episode number prepended with episode type: 
                eg. 'EP15' or 'SP1'
                
        Returns:
            BangumiEpisodeCollection or None: result matching ep_info. None if
                not found
        """
        if ep_info.isdigit():
            search_result = [ep_c for ep_c in self.ep_collections
                             if ep_c.episode.id_ == ep_info]
        else:
            ep_type, ep_num = re.search('([a-zA-Z]*)([0-9]+)',
                                            ep_info).groups()
            ep_num = int(ep_num)
            ep_type = ep_type.upper()
            search_result = [ep_c for ep_c in self.ep_collections
                             if ep_c.episode.ep_num == ep_num
                             and ep_c.episode.ep_type == ep_type]
        if not search_result:
            return None
        else:
            return search_result[0]
    
    @require_session
    def sync_n_watched_eps(self):
        """Sync n_watched_eps, as sync_collection won't do this
        
        Returns:
            bool: True if successful
        """
        return self._session.set_n_watched_eps(self)


class BangumiEpisodeCollection(BangumiCollection):
    """Class representing a episode collection
    
    Note:
        The constructor is NOT supposed to be called directly by client code,
        Please use class methods in this class and other methods provided in
        BangumiSession to create instances of BangumiEpisodeCollection
        
    Attributes:
        sub_collection (BangumiAnimeCollection): subject collections
            containing this episode collection
    """

    _VALID_C_STATUS = ('watched', 'watched_up_to', 'queue', 'drop')

    def __init__(self, episode, c_status=None, sub_collection=None):
        self._episode = episode
        self._c_status = c_status if c_status else None
        self._sub_collection = (weakref.ref(sub_collection)
                                if sub_collection else None)
        self._session = None

    @classmethod
    def from_html(cls, ep_id, html):
        """Create BangumiEpisodeCollection object for specified episode from
        html of subject episodes page
        
        Args:
            ep_id (str): the id of episode to create collection for
            html (unicode): the html for the episodes page
            
        Returns:
            BangumiEpisodeCollection: object created with data provided        
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup(ep_id, soup)

    @classmethod
    def from_soup(cls, ep_id, soup):
        """Create BangumiEpisodeCollection object for specified episode from
        parsed html of subject episodes page
        
        Args:
            ep_id (str): the id of episode to create collection for
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            BangumiEpisodeCollection: object created with data provided
        """
        episode = BangumiEpisode.from_soup(ep_id, soup)
        return cls.from_soup_with_ep(episode, soup)

    @classmethod
    def from_html_with_ep(cls, episode, html):
        """Create BangumiEpisodeCollection object for specified episode from
        html of subject episodes page, with episode object provided
        
        Args:
            episode (BangumiEpisode): the episode to create collection for
            html (unicode): the html for the episodes page
            
        Returns:
            BangumiEpisodeCollection: object created with data provided        
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup_with_ep(episode, soup)

    @classmethod
    def from_soup_with_ep(cls, episode, soup):
        """Create BangumiEpisodeCollection object for specified episode from
        parsed html of subject episodes page, with episode object provided
        
        Args:
            episode (BangumiEpisode): the episode to create collection for
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            BangumiEpisodeCollection: object created with data provided
        """
        ep_href = '/ep/{0}'.format(episode.id_)
        c_status = (soup.find(href=ep_href).parent.parent
                    .find(class_='listEpPrgManager')
                    .span['class'][0][6:].lower())
        return cls(episode, c_status)

    @classmethod
    def ep_colls_for_sub_from_html(cls, subject, html):
        """Create a list of BangumiEpisodeCollection object from html of the
        subject episodes page, with subject object provided
        
        Note:
            This assumes that the subject already has complete eps
        
        Args:
            subject (BangumiAnime): the subject to create episode
                collections for
            html (unicode): the html for the episodes page
            
        Returns:
            list[BangumiEpisodeCollection]: for all episodes in that subject
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.ep_colls_for_sub_from_soup(subject, soup)

    @classmethod
    def ep_colls_for_sub_from_soup(cls, subject, soup):
        """Create a list of BangumiEpisodeCollection object from parsed html
        of the subject episodes page, with subject object provided
        
        Note:
            This assumes that the subject already has complete eps
        
        Args:
            subject (BangumiAnime): the subject to create episode
                collections for
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            list[BangumiEpisodeCollection]: for all episodes in that subject
        """
        ep_collections = []
        coll_infos = (soup.find(class_='line_list')
                      .find_all(class_=re.compile('^status*')))
        if len(coll_infos) == len(subject.eps):
            for ep, info in zip(subject.eps, coll_infos):
                c_status = info['class'][0][6:].lower()
                ep_collection = cls(ep, c_status)
                ep_collections.append(ep_collection)
        else:
            for ep in subject.eps:
                ep_collection = cls.from_soup_with_ep(ep, soup)
                ep_collections.append(ep_collection)
        return ep_collections

    @classmethod
    def from_json(cls, json_text):
        """Convert back from json
        
        Args:
            json_text (unicode): json text to convert from
            
        Returns:
            BangumiEpisodeCollection: created from data in json text
        """
        kwargs = json.loads(json_text)
        kwargs.pop('version', (0, 0, 1))
        kwargs = {(key[1:] if key.startswith('_') else key): value
                  for key, value in kwargs.items()}
        kwargs['episode'] = BangumiEpisode.from_json(kwargs['episode'])
        return cls(**kwargs)
    
    def to_json(self):
        """Convert to json
        
        Note:
            sub_collection and session are dropped
            
        Returns:
            unicode: converted json text
        """
        kwargs = self.__dict__.copy()
        kwargs['version'] = CUR_VERSION
        kwargs.pop('_sub_collection')
        kwargs.pop('_session')
        kwargs['_episode'] = kwargs['_episode'].to_json()
        return json.dumps(kwargs, ensure_ascii=False)
    
    @property
    def episode(self):
        """BangumiEpisode: the episode associated with this collection
        """
        return self._episode

    @property
    def c_status(self):
        """str: collection status of episode must be one of 'watched',
        'watched_up_to', 'queue', 'drop'
        
        setter raises ValueError for invalid values
        """
        return self._c_status

    @c_status.setter
    def c_status(self, value):
        if value not in self._VALID_C_STATUS:
            raise ValueError("Invalid value provided: {0}".format(value))
        else:
            self._c_status = value
            
    @property
    def sub_collection(self):
        """BangumiAnimeCollection: subject collection containing this
        episode collection
        
        setter will raise TypeError for incorrect type
        """
        if self._sub_collection is None:
            return self._sub_collection
        else:
            return self._sub_collection()
    
    @sub_collection.setter
    def sub_collection(self, value):
        if not isinstance(value, BangumiAnimeCollection):
            raise TypeError("value must be BangumiAnimeCollection, got {0}"
                            .format(type(value)))
        self._sub_collection = weakref.ref(value)