# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup
from .base import BangumiBase
from _pyio import __metaclass__


class FixedAttribute(object):
    """A descriptor for attributes not supposed to be changed
    """
    def __init__(self):
        self.attr_name = None
        self.internal_name = None
        
    def __get__(self, obj, objtype):
        if obj is None:
            return self
        return getattr(obj, self.internal_name)
    
    def __set__(self, obj, value):
        if getattr(obj, self.internal_name) is None:
            setattr(obj, self.internal_name, value)
        else:
            raise AttributeError("Attribute {0} is NOT supposed to be changed"
                                 .format(self.attr_name))

  
class ElementMeta(type):
    """Metaclass for BangumiElement.
    From the book Effective Python
    """
    def __new__(meta, name, bases, class_dict):  # @NoSelf
        for key, value in class_dict.items():
            if isinstance(value, FixedAttribute):
                value.attr_name = key
                value.internal_name = '_' + key
        cls = type.__new__(meta, name, bases, class_dict) 
        return cls


class BangumiElement(BangumiBase):
    """Interface for elements including BangumiSubject and BangumiEpisode"""
    
    __metaclass__ = ElementMeta

    def to_collection(self, session):
        """Transform to collection of same type."""
        raise NotImplementedError



class BangumiSubject(BangumiElement):
    """Class representing a subject
    
    Attributes:
        sub_id (str): subject id. NOT supposed to be changed
        title (unicode): official title of the subject. NOT supposed to be
            changed
        ch_title (unicode): title of the subject in Chinese or other language.
            NOT supposed to be changed.
        other_info (dict): key-values for other info
    """
    
    sub_id = FixedAttribute()
    title = FixedAttribute()
    ch_title = FixedAttribute()

    def __init__(self, sub_id, title=None, ch_title=None, n_eps=None,
                 eps=None):
        self._sub_id = sub_id
        self._title = title
        self._ch_title = ch_title
        self._n_eps = n_eps
        self._eps = list(eps) if eps else []
        for ep in self.eps:
            ep.subject = self
        self.other_info = None

    @classmethod
    def from_html(cls, sub_html, ep_html):
        """Create BangumiSubject object from html of the subject main page and
        episodes page
        
        Args:
            sub_html (unicode): html for the subject main page
            ep_html (unicode): html for the subject's episodes page
            
        Returns:
            BangumiSubject: with data from html
        """
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)

    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        """Create BangumiSubject object from parsed html of subject main page
        and episodes page
        
        Args:
            sub_html (unicode): parsed html for the subject main page
            ep_html (unicode): parsed html for the subject's episodes page
            
        Returns:
            BangumiSubject: with data from parsed html
        """
        sub_id = sub_soup.find(class_='nameSingle').a['href'].split('/')[-1]
        sub_title = sub_soup.find(class_='nameSingle').a.text
        sub_ch_title = sub_soup.find(class_='nameSingle').a['title']
        sub_n_eps = cls._get_n_eps(sub_soup)
        sub_eps = BangumiEpisode.eps_from_soup(ep_soup)
        subject = cls(sub_id, sub_title, sub_ch_title, sub_n_eps, sub_eps)
        return subject

    def to_collection(self, session):
        """Convert to a BangumiSubjectCollection
        
        Args:
            session (BangumiSession): session for downloading necessary data
            
        Returns:
            BangumiSubjectCollection: collection containing this subject
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
        
    Attributes:
        ep_id (str): episode id. NOT supposed to be changed
        ep_num (int): episode number. NOT supposed to be changed
        ep_type (str): episode type, usually any of "EP", "SP", "OP", "ED";
            "EP" stands for regular episode. NOT supposed to be changed
        title (unicode): official title of the episode. NOT supposed to be
            changed
        ch_title (unicode): title of the episode in Chinese or other language.
            NOT supposed to be changed.
        other_info (dict): other information for this episode
    """
    
    ep_id = FixedAttribute()
    ep_num = FixedAttribute()
    ep_type = FixedAttribute()
    title = FixedAttribute()
    ch_title = FixedAttribute()

    def __init__(self, ep_id, ep_num, ep_type=None, status=None, title=None,
                 ch_title=None, subject=None):
        self._ep_id = ep_id
        self._ep_num = ep_num
        self._ep_type = ep_type
        self._status = status
        self._title = title if title else ""
        self._ch_title = ch_title if ch_title else ""
        self._subject = subject
        self.other_info = None

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
            ep_id (str): the id of episode to create object for
            html (unicode): the html for the episodes page
            
        Returns:
            BangumiEpisode: object created with data provided        
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.ep_from_soup(ep_id, soup)

    @classmethod
    def from_soup(cls, ep_id, soup):
        """Create one BangumiEpisode object for specified episode from parsed
        html of subject episodes page
        
        Args:
            ep_id (str): the id of episode to create object for
            soup (BeautifulSoup): the parsed html for the episodes page
            
        Returns:
            BangumiEpisode: object created with data provided
        """
        ep_url = '/ep/{0}'.format(ep_id)
        ep_info = soup.find(href=ep_url).parent
        ep = cls(*cls._extract_ep_info(ep_info))
        return ep
        
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
        """BangumiSubject: subject that this episode belongs to.
        
        setter will raise TypeError for incorrect type
        """
        return self._subject
    
    @subject.setter
    def subject(self, value):
        if not isinstance(value, BangumiSubject):
            raise TypeError("Provided value must be a BangumiSubject, got {0}"
                            .format(type(value)))
        self._subject = value
            
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
            ep_id, ep_num, ep_type, ep_status, ep_title, ep_ch_title: data
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