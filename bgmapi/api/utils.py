# -*- coding: utf-8 -*-
import re
from bs4 import BeautifulSoup


def to_unicode(s):
    """Return a unicode regardless of the type of input string"""
    if isinstance(s, str):
        result = s.decode('utf-8')
    else:
        result = s
    return result


def get_encoding_from_html(html):
    """Get encoding info from html"""
    try:
        return re.search('<meta charset="(.+)"', html).group(1)
    except:
        return ""


def get_checked_values(soup):
    """Get the values for checked input tags"""
    return [i['value'] for i in soup.find_all('input')
            if i.has_attr('checked')]


def get_user_id_from_html(html):
    """Get user_id from html of home/subject/episode page when logged in"""
    soup = BeautifulSoup(html, 'html.parser')
    return get_user_id_from_soup(soup)


def get_user_id_from_soup(soup):
    """Get user_id from bs4-parsed html of home/subject/episode page when
    logged in
    """
    user_id = (soup
               .find(class_='idBadgerNeue')
               .find(class_='avatar')['href']
               .split('/')[-1])
    return user_id


def get_ep_ids_till_this(episode):
    """Get list of ep_ids in the same subject prior to this one, inclusive"""
    subject = episode.subject
    eps = subject.eps
    ep_ids = []
    for ep in eps:
        ep_ids.append(ep.ep_id)
        if ep.ep_id == episode.ep_id:
            break
    return ep_ids
