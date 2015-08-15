# -*- coding: utf-8 -*-
import re
from api.session import *


class BangumiElement(object):
    """Interface for elements including BangumiSubject and BangumiEpisode"""
    @classmethod
    def from_html(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def from_soup(cls, *args, **kwargs):
        raise NotImplementedError

    @classmethod
    def deserialize(cls, text):
        raise NotImplementedError

    def to_collection(self, *args):
        raise NotImplementedError

    def serialize(self):
        raise NotImplementedError


class BangumiSubject(BangumiElement):
    """Class representing a subject"""

    def __init__(self, sub_id, title=None, ch_title=None, n_eps=None,
                 eps=None):
        self.sub_id = sub_id
        self.title = title
        self.ch_title = ch_title
        self.n_eps = n_eps
        self.eps = eps if eps else []
        for ep in self.eps:
            ep.subject = self

    @classmethod
    def from_html(cls, sub_html, ep_html):
        """Create BangumiSubject object from html of the subject main page and
        episodes page
        """
        sub_soup = BeautifulSoup(sub_html, 'html.parser')
        ep_soup = BeautifulSoup(ep_html, 'html.parser')
        return cls.from_soup(sub_soup, ep_soup)

    @classmethod
    def from_soup(cls, sub_soup, ep_soup):
        """Create BangumiSubject object from parsed html of subject main page
        and episodes page
        """
        sub_id = sub_soup.find(class_='nameSingle').a['href'].split('/')[-1]
        sub_title = sub_soup.find(class_='nameSingle').a.text
        sub_ch_title = sub_soup.find(class_='nameSingle').a['title']
        sub_n_eps = cls.get_n_eps(sub_soup)
        sub_eps = BangumiEpisode.eps_from_soup(ep_soup)
        subject = cls(sub_id, sub_title, sub_ch_title, sub_n_eps, sub_eps)
        return subject

    def to_collection(self, session):
        sub_coll = session.get_sub_collection_with_subject(self)
        return sub_coll

    def to_text(self):
        pass

    @staticmethod
    def get_n_eps(soup):
        info = soup.find(id='infobox').text
        try:
            return int(re.search(u'话数: ([0-9]*?)\n', info).group(1))
        except:
            return None


class BangumiEpisode(BangumiElement):
    """Class representing an episode"""
    def __init__(self, ep_id, num, ep_type=None, status=None, title=None,
                 ch_title=None, subject=None):
        self.ep_id = ep_id
        self.num = num
        self.ep_type = ep_type
        self.status = status
        self.title = title if title else ""
        self.ch_title = ch_title if ch_title else ""
        self.subject = subject

    @classmethod
    def eps_from_html(cls, html):
        """Create a list of BangumiEpisode object from html of the subject
        episodes page
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.eps_from_soup(soup)

    @classmethod
    def eps_from_soup(cls, soup):
        """Create list of BangumiEpisode object from parsed html of subject
        episodes page
        """
        infos = soup.find(class_='line_list').find_all('h6')
        eps = []
        for ep_info in infos:
            ep = cls(*cls.extract_ep_info(ep_info))
            eps.append(ep)
        return eps

    @classmethod
    def from_html(cls, ep_id, html):
        """Create one BangumiEpisode object specified episode from html of
        subject episodes page
        """
        soup = BeautifulSoup(html, 'html.parser')
        return cls.ep_from_soup(ep_id, soup)

    @classmethod
    def from_soup(cls, ep_id, soup):
        """Create one BangumiEpisode object for specified episode from parsed
        html of subject episodes page
        """
        ep_url = '/ep/{0}'.format(ep_id)
        ep_info = soup.find(href=ep_url).parent
        ep = cls(*cls.extract_ep_info(ep_info))
        return ep

    @staticmethod
    def extract_ep_info(info_soup):
        """Extract information necessary for constructing a BangumiEpisode
        from parsed html of a single episode entry in subject episodes page.

        A sample piece:
         `<h6><span class="epAirStatus" title="已放送">
        <span class="Air"></span></span>
        <a href="/ep/46037">SP0.よせあつめブルース</a>
        <span class="tip"> / Mish-Mash Blues</span> </h6>`
        """
        ep_id = info_soup.a['href'].split('/')[-1]
        ep_type_num, ep_title = info_soup.a.text.split('.', 1)
        ep_type, ep_num = re.search('([a-zA-Z]*)([0-9]+)',
                                    ep_type_num).groups()
        ep_num = int(ep_num)
        ep_type = ep_type if ep_type else "EP"
        ep_status = info_soup.span.span['class']
        ch_title_wrapper = info_soup.find(class_='tip')
        ep_ch_title = ch_title_wrapper.text[3:] if ch_title_wrapper else ""
        return ep_id, ep_num, ep_type, ep_status, ep_title, ep_ch_title

    def to_collection(self, session):
        ep_coll = session.get_ep_collection_with_episode(self)
        return ep_coll
