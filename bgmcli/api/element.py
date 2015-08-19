# -*- coding: utf-8 -*-
"""Classes that represents elements such as subjects and episodes
"""
import re
import weakref
import json
from _pyio import __metaclass__
import pkg_resources
from bs4 import BeautifulSoup
from .base import BangumiBase
from .utils import get_subject_type_from_soup


__all__ = ['BangumiAnime', 'BangumiEpisode']
CUR_VERSION = pkg_resources.require("bgmcli")[0].version


class BangumiElement(BangumiBase):
    """class for elements including BangumiSubject and BangumiEpisode
    
    Note:
        This abstract class is NOT supposed to be instantiated
    """
    
    def __init__(self, id_, title=None, ch_title=None):
        self._id_ = id_
        self._title = title
        self._ch_title = ch_title
        
    @property
    def id_(self):
        """str: element (episode, subject etc.) id. NOT supposed to be changed
        """
        return self._id_
    
    @property
    def title(self):
        """unicode: official title of the element. NOT supposed to be
        modified
        """
        return self._title
    
    @property
    def ch_title(self):
        """unicode): title of the subject in Chinese or other language.
        NOT supposed to be modified.
        """
        return self._ch_title

    def to_collection(self, session):
        """Transform to collection of same type."""
        raise NotImplementedError
    
    def __eq__(self, other):
        """Excludes attribute BangumiAnime.eps and BangumiEpisode.subject"""
        if not isinstance(other, self.__class__):
            return False
        else:
            for key, value in self.__dict__.items():
                if key in ['_eps', '_subject']:
                    continue
                if value != getattr(other, key):
                    return False
            return True
        
    def __ne__(self, other):
        return not self.__eq__(other)


class SubjectMeta(type):
    """Metaclass for BangumiSubject. Helps to register subclasses in 
    BangumiSubjectIndex
    """
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        (BangumiSubjectFactory.sub_type_subclass_map
         .update({class_dict['_SUB_TYPE']: name}))
        cls = type.__new__(meta, name, bases, class_dict) 
        return cls
    
    
class BangumiSubjectFactory(object):
    """A factory class that identifies which subclass of BangumiSubject
    need to be instantiated
    
    Attributes:
        sub_type_subclass_map (dict): a mapping from subject type to the
            subclass name that defines this kind of subject
    """
    sub_type_subclass_map = {}
    
    @classmethod
    def from_html(cls, sub_html, ep_html):
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)
    
    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        sub_type = get_subject_type_from_soup(sub_soup)
        if sub_type not in cls.sub_type_subclass_map:
            raise NotImplementedError
        subclass = globals()[cls.sub_type_subclass_map[sub_type]]
        return subclass.from_soup(sub_soup, ep_soup)


class BangumiSubject(BangumiElement):
    """"The class representing a general subject.
    A subject is an anime or book or game title, which may contain a number
    of episodes (for anime) or volumes (for manga).
    In Bangumi, there are four kinds of subjects, namely 'anime', 'book',
    'game' and 'real'.
    
    Note:
        This abstract class is NOT supposed to be instantiated
    """

    __metaclass__ = SubjectMeta
    _SUB_TYPE = None
    
    @classmethod
    def from_html(cls, sub_html, ep_html):
        """Create BangumiSubject object from html of the subject main page and
        episodes page
        
        Args:
            sub_html (unicode): html for the subject main page
            ep_html (unicode): html for the subject's episodes page
            
        Returns:
            BangumiAnime: with data from html
        """
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)
    
#     @classmethod
#     def from_soup(cls, sub_soup, ep_soup):
#         sub_type = get_subject_type_from_soup(sub_soup)
#         if sub_type == 'anime':
#             return BangumiAnime.from_soup(sub_soup, ep_soup)
#         else:
#             raise NotImplementedError


class BangumiAnime(BangumiSubject):
    """Class representing an anime subject
    
    Args:
        id_ (str): subject id.
        title (unicode): official title of the anime subject. 
        ch_title (unicode): title of the subject in Chinese or other language.
        eps (list[BangumiEpisode]): episodes belonging to this anime
    
    Attributes:
        other_info (dict): key-values for other info
    """
    
    _SUB_TYPE = 'anime'

    def __init__(self, id_, title=None, ch_title=None, n_eps=None,
                 eps=None):
        super(BangumiAnime, self).__init__(id_, title, ch_title)
        self._n_eps = n_eps
        self._eps = list(eps) if eps else []
        for ep in self.eps:
            ep.subject = self
        self.other_info = {}

    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        """Create BangumiAnime object from parsed html of subject main page
        and episodes page
        
        Args:
            sub_html (unicode): parsed html for the subject main page
            ep_html (unicode): parsed html for the subject's episodes page
            
        Returns:
            BangumiAnime: with data from parsed html
        """
        sub_id = sub_soup.find(class_='nameSingle').a['href'].split('/')[-1]
        sub_title = sub_soup.find(class_='nameSingle').a.text
        sub_ch_title = sub_soup.find(class_='nameSingle').a['title']
        sub_n_eps = cls._get_n_eps(sub_soup)
        sub_eps = BangumiEpisode.eps_from_soup(ep_soup)
        subject = cls(sub_id, sub_title, sub_ch_title, sub_n_eps, sub_eps)
        return subject
    
    @classmethod
    def from_json(cls, json_text):
        """Convert back from json
        
        Args:
            json_text (unicode): json text to convert from
            
        Returns:
            BangumiAnime: created from data in json text
        """
        kwargs = json.loads(json_text)
        kwargs.pop('version', (0, 0, 1))
        other_info = kwargs.pop('other_info')
        kwargs = {(key[1:] if key.startswith('_') else key): value
                  for key, value in kwargs.items()}
        kwargs['eps'] = [BangumiEpisode.from_json(j_text)
                         for j_text in kwargs['eps']]
        subject = BangumiAnime(**kwargs)
        subject.other_info = other_info
        for ep in subject._eps:
            ep.subject = subject
        return subject
    
    def to_json(self):
        """Convert to json
        
        Returns:
            unicode: converted json text
        """
        kwargs = self.__dict__.copy()
        kwargs['_eps'] = [ep.to_json() for ep in kwargs['_eps']]
        kwargs['version'] = CUR_VERSION
        return json.dumps(kwargs, ensure_ascii=False)

    def to_collection(self, session):
        """Convert to a BangumiSubjectCollection
        
        Args:
            session (BangumiSession): session for downloading necessary data
            
        Returns:
            BangumiSubjectCollection: collection containing this anime subject
        """
        sub_coll = session.get_sub_collection_with_subject(self)
        return sub_coll
    
    @property
    def n_eps(self):
        """int: number of episodes in this subject, usually only considering
        regular episodes, i.e. with ep_type == 'EP'
        
        setter converts value to int and raises ValueError if less than 0
        """
        return self._n_eps
    
    @n_eps.setter
    def n_eps(self, value):
        value = int(value)
        if value < 0:
            raise ValueError("n_eps must be at least 0, got {0}"
                             .format(value))
        self._n_eps = value
        
    @property
    def eps(self):
        """tuple[BangumiEpisode]: episodes belong to this subject
        
        setter will check type of each entry and raise TypeError if incorrect
        """
        return tuple(self._eps)
    
    @eps.setter
    def eps(self, value):
        value = list(value)
        for ep in value:
            if not isinstance(ep, BangumiEpisode):
                raise TypeError("Each entry must be BangumiEpisode, got {0}"
                                .format(type(ep)))
        self._eps = value

    @staticmethod
    def _get_n_eps(soup):
        info = soup.find(id='infobox').text
        try:
            return int(re.search(u'话数: ([0-9]*?)\n', info).group(1))
        except:
            return None
        
    @staticmethod
    def _parse_info_box(soup):
        info = soup.find(id='infobox').text
        parsed_dict = dict([line.strip().split(': ')
                            for line in info.split('\n')])
        return parsed_dict


class BangumiEpisode(BangumiElement):
    
    """Class representing one episode
    
    Note:
        The constructor of this class is NOT supposed to be called by client
        code. Please use class methods in this class and methods provided in
        BangumiSession to create instances of BangumiEpisode.
        And data contained are typically NOT supposed to be changed after
        instantiation.
        
    Args:
        id_ (str): episode id.
        ep_num (int): episode number
        ep_type (str): episode type, usually any of "EP", "SP", "OP", "ED";
            "EP" stands for regular episode. NOT supposed to be changed
        status (str): airing status of the episode must be in 'air', 'today',
            'na', where 'air' stands for aired, 'today' stands for to be aired
            today, and 'na' stands for not aired
        title (unicode): official title of the episode. NOT supposed to be
            changed
        ch_title (unicode): title of the episode in Chinese or other language.
            NOT supposed to be changed.
        other_info (dict): other information for this episode
        
    Attributes:
        other_info (dict): other information for this episode
    """

    def __init__(self, id_, ep_num, ep_type=None, status=None, title=None,
                 ch_title=None, subject=None):
        super(BangumiEpisode, self).__init__(id_, title, ch_title)
        self._id_ = id_
        self._ep_num = ep_num
        self._ep_type = ep_type
        self._status = status
        self._title = title if title else ""
        self._ch_title = ch_title if ch_title else ""
        self._subject = weakref.ref(subject) if subject else None
        self.other_info = {}

    @classmethod
    def eps_from_html(cls, html):
        """Create a list of BangumiEpisode object from html of the subject
        episodes page
        
        Args:
            html (unicode): the  html for the episodes page
            
        Returns:
            list[BangumiEpisode]: for all episodes in that subject
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.eps_from_soup(soup)

    @classmethod
    def eps_from_soup(cls, soup):
        """Create list of BangumiEpisode object from parsed html of subject
        episodes page
        
        Args:
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            list[BangumiEpisode]: for all episodes in that subject
        """
        infos = soup.find(class_='line_list').find_all('h6')
        eps = []
        for ep_info in infos:
            ep = cls(*cls._extract_ep_info(ep_info))
            eps.append(ep)
        return eps

    @classmethod
    def from_html(cls, ep_id, html):
        """Create one BangumiEpisode object for specified episode from html of
        subject episodes page
        
        Args:
            id_ (str): the id_ of episode to create object for
            html (unicode): the html for the episodes page
            
        Returns:
            BangumiEpisode: object created with data provided        
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup(ep_id, soup)

    @classmethod
    def from_soup(cls, ep_id, soup):
        """Create one BangumiEpisode object for specified episode from parsed
        html of subject episodes page
        
        Args:
            id_ (str): the id_ of episode to create object for
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            BangumiEpisode: object created with data provided
        """       
        ep_url = '/ep/{0}'.format(ep_id)
        ep_info = soup.find(href=ep_url).parent
        ep = cls(*cls._extract_ep_info(ep_info))
        return ep
    
    @classmethod
    def from_json(cls, json_text):
        """Convert from json
        
        Note:
            subject is dropped converting to json, so won't be included here
            
        Returns:
            BangumiEpisode: created from data in json text
        """
        kwargs = json.loads(json_text)
        kwargs.pop('version', (0, 0, 1))
        other_info = kwargs.pop('other_info')
        kwargs = {(key[1:] if key.startswith('_') else key): value
                  for key, value in kwargs.items()}
        ep = cls(**kwargs)
        ep.other_info = other_info
        return ep
    
    def to_json(self):
        """Convert to json

        Note:
            subject is dropped if when converting episode
            
        Returns:
            unicode: result of converting to json
        """
        kwargs = self.__dict__.copy()
        kwargs['version'] = CUR_VERSION
        kwargs.pop('_subject')
        return json.dumps(kwargs, ensure_ascii=False)
    
    @property
    def ep_num(self):
        """int: episode number. NOT supposed to be modified.
        """
        return self._ep_num
    
    @property
    def ep_type(self):
        """str: episode type, usually any of "EP", "SP", "OP", "ED";
        "EP" stands for regular episode. NOT supposed to be modified
        """
        return self._ep_type
        
    @property
    def status(self):
        """str: airing status of the episode must be in 'air', 'today', 'na',
        where 'air' stands for aired, 'today' stands for to be aired today,
        and 'na' stands for not aired
        
        setter will raise ValueError for invalid values
        """
        return self._status
    
    @status.setter
    def status(self, value):
        if value not in ['air', 'today', 'na']:
            raise ValueError("Invalid value provided: {0}".format(value))
        else:
            self._status = value
            
    @property
    def subject(self):
        """BangumiAnime: subject that this episode belongs to.
        
        setter will raise TypeError for incorrect type
        """
        if self._subject is None:
            return self._subject
        else:
            return self._subject()
    
    @subject.setter
    def subject(self, value):
        if not isinstance(value, BangumiAnime):
            raise TypeError("Provided value must be a BangumiAnime, got {0}"
                            .format(type(value)))
        self._subject = weakref.ref(value)
            
    def to_collection(self, session):
        """Convert to a BangumiEpisodeCollection
        
        Args:
            session (BangumiSession): session for downloading necessary data
            
        Returns:
            BangumiEpisodeCollection: collection containing this subject
        """
        ep_coll = session.get_ep_collection_with_episode(self)
        return ep_coll
    
    @staticmethod
    def _extract_ep_info(info_soup):
        """Extract information necessary for constructing a BangumiEpisode
        from parsed html of a single episode entry in subject episodes page.

        A sample piece:
         `<h6><span class="epAirStatus" title="已放送">
        <span class="Air"></span></span>
        <a href="/ep/46037">SP0.よせあつめブルース</a>
        <span class="tip"> / Mish-Mash Blues</span> </h6>`
        
        Args:
            info_soup (BeautifulSoup): parsed html of the above-mentioned
                piece of the subjects ep page
                
        Returns:
            id_, ep_num, ep_type, ep_status, ep_title, ep_ch_title: data
                necessary for constructing a BangumiEpisode object
        """
        ep_id = info_soup.a['href'].split('/')[-1]
        ep_type_num, ep_title = info_soup.a.text.split('.', 1)
        ep_type, ep_num = re.search('([a-zA-Z]*)([0-9]+)',
                                    ep_type_num).groups()
        ep_num = int(ep_num)
        ep_type = ep_type if ep_type else "EP"
        ep_status = info_soup.span.span['class'][0].lower()
        ch_title_wrapper = info_soup.find(class_='tip')
        ep_ch_title = ch_title_wrapper.text[3:] if ch_title_wrapper else ""
        return ep_id, ep_num, ep_type, ep_status, ep_title, ep_ch_title