# -*- coding: utf-8 -*-
from api.element import *
from api.session import *
from api.utils import *


class BangumiCollection(object):
    """Mixin for collection behaviors"""

    def set_session(self, session):
        self.session = session
        if isinstance(self, BangumiSubjectCollection) and self.ep_collections:
            for ep_c in self.ep_collections:
                ep_c.set_session(session)

    def sync_collection(self):
        self.validate()
        if not self.session:
            raise ValueError("Session not set")
        else:
            self.session.set_collection(self)

    def remove_with_sync(self):
        if not self.session:
            raise ValueError("Session not set")
        self.session.remove_collection(self)


class BangumiSubjectCollection(BangumiCollection, BangumiElement):
    """Class representing a subject collection

    Note: The constructor is NOT supposed to be called directly

    Attributes:
        subject (BangumiSubject): the subject associated with this collection
        ep_collections (list of BangumiEpisodeCollection): episode collections
            associated with this subject
    """

    VALID_C_STATUS = tuple(range(1, 6))

    def __init__(self, subject, c_status=None, rating=None, tags=None,
                 comment=None, n_watched_eps=None, ep_collections=None):
        self.subject = subject
        self._c_status = c_status
        self._rating = rating
        self._tags = tags if tags else []
        self._comment = comment if comment else u""
        self._n_watched_eps = n_watched_eps
        self.ep_collections = ep_collections if ep_collections else []
        for ep_coll in self.ep_collections:
            ep_coll.sub_collection = self
        self.session = None

    @classmethod
    def from_html(cls, sub_html, ep_html):
        """Create BangumiSubjectCollection object from html"""
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)

    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        subject = BangumiSubject.from_soup(sub_soup, ep_soup)
        return cls.from_soup_with_subject(subject, sub_soup, ep_soup)

    @classmethod
    def from_html_with_subject(cls, subject, sub_html, ep_html):
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup_with_subject(subject, sub_soup, ep_soup)

    @classmethod
    def from_soup_with_subject(cls, subject, sub_soup, ep_soup):
        try:
            get_user_id_from_soup(sub_soup)
        except TypeError:
            raise ValueError("Please provide subject page html after login!")
        else:
            if sub_soup.find(id='SecTab'):
                return BangumiSubjectCollection(subject)
            collect_form = sub_soup.find(id='collectBoxForm')
            status = int(get_checked_values(
                collect_form.find(class_='collectType'))[0])
            rating_container = get_checked_values(
                collect_form.find(id='interest_rate'))
            rating = int(rating_container[0]) if rating_container else None
            tags = collect_form.find(id='tags')['value'].strip().split(' ')
            comment = collect_form.find(id='comment').text
            n_watched_eps = int(sub_soup.find(id='watchedeps')['value'])
            ep_collections = BangumiEpisodeCollection.ep_colls_for_sub_from_soup(subject, ep_soup)
            return cls(subject, status, rating, tags, comment, n_watched_eps,
                       ep_collections)

    @property
    def c_status(self):
        return self._c_status

    @c_status.setter
    def c_status(self, value):
        if value in self.VALID_C_STATUS:
            self._c_status = value
        else:
            raise ValueError("Invalid value provided")

    @property
    def rating(self):
        return self._rating

    @rating.setter
    def rating(self, value):
        if value is None:
            self._rating = value
        elif isinstance(value, int):
            if value >= 1 and value <= 10:
                self._rating = value
            else:
                raise ValueError("Value must be between 1 to 10, got {0}"
                                 .format(value))
        else:
            raise TypeError("rating must in int or None, got {0}"
                            .format(type(value)))
    
    @property
    def tags(self):
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
        return self._comment
    
    @comment.setter
    def comment(self, value):
        value = to_unicode(value)
        if not isinstance(value, unicode):
            raise TypeError("comment must be a unicode strings, got {0}"
                            .format(type(value)))
        self._comment = value

    @property
    def n_watched_eps(self):
        return self._n_watched_eps
    
    @n_watched_eps.setter
    def n_watched_eps(self, value):
        if not isinstance(value, int):
            raise TypeError("n_watched_eps must be an integer, got {0}"
                            .format(type(value)))
        elif value < 0 or (self.subject.n_eps and value > self.subject.n_eps):
            raise ValueError("n_watched_eps must non-negative and less than " + 
                             "n_eps, got {0}".format(value))
        self._n_watched_eps = value

    def set_data(self, data_key, data_value, sync=False):
        setattr(self, data_key, data_value)
        if sync:
            self.sync_data()

    def to_collection(self):
        return self


class BangumiEpisodeCollection(BangumiCollection, BangumiElement):
    """Class representing a episode collection"""

    VALID_C_STATUS = ('watched', 'watched_till', 'queue', 'drop')

    def __init__(self, episode, c_status=None, sub_collection=None):
        self.episode = episode
        self._c_status = c_status if c_status in self.VALID_C_STATUS else ''
        self.sub_collection = sub_collection
        self.session = None

    @classmethod
    def from_html(cls, ep_id, html):
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup(ep_id, soup)

    @classmethod
    def from_soup(cls, ep_id, soup):
        episode = BangumiEpisode.from_soup(ep_id, soup)
        return cls.from_soup_with_ep(episode, soup)

    @classmethod
    def from_html_with_ep(cls, episode, html):
        soup = BeautifulSoup(html, 'html.parser')
        return cls.from_soup_with_ep(episode, soup)

    @classmethod
    def from_soup_with_ep(cls, episode, soup):
        ep_href = '/ep/{0}'.format(episode.ep_id)
        c_status = (soup.find(href=ep_href).parent.parent
                    .find(class_='listEpPrgManager')
                    .span['class'][0][6:].lower())
        return cls(episode, c_status)

    @classmethod
    def ep_colls_for_sub_from_html(cls, subject, html):
        """Assumes that the subject already has complete eps info"""
        soup = BeautifulSoup(html, 'html.parser')
        return cls.ep_colls_for_sub_from_soup(subject, soup)

    @classmethod
    def ep_colls_for_sub_from_soup(cls, subject, soup):
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

    @property
    def c_status(self):
        return self._c_status

    @c_status.setter
    def c_status(self, value):
        if value not in self.VALID_C_STATUS:
            raise ValueError("Invalid value provided: {0}".format(value))
        else:
            self._c_status = value

    def to_collection(self):
        return self
