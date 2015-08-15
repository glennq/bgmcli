# -*- coding: utf-8 -*-
import re
import requests
from bs4 import BeautifulSoup
from api.utils import *
from api.exception import *
from api.element import BangumiSubject, BangumiEpisode
from api.collection import *


class BangumiSession(object):
    """The class that abtracts a login session for Bangumi and provides methods
    to retrieve and set element/collection data
    """

    VALID_DOMAIN = ['bgm.tv', 'bangumi.tv', 'chii.in']

    def __init__(self, email, password, domain='bgm.tv'):
        """Constructs a `BangumiSession`

        Args:
            email (str): the login email address
            password (str): the password for login
            domain (str): the domain to use for login must be one of
                          ['bgm.tv', 'bangumi.tv', 'chii.in']

        Returns:
            None
        """
        if domain not in self.VALID_DOMAIN:
            raise ValueError("Domain must be one of {0}".format(self.VALID_DOMAIN))
        self.session = requests.Session()
        self.base_url = (domain if domain.startswith('http://')
                         else 'http://' + domain)
        self.email = email
        self.logged_in = False
        self._login(email, password)
        self.gh = self._get_gh()
        self.user_id = self._get_user_id()

    def get_subject(self, sub_id):
        """Get crucial data for specified subject
        Args:
            sub_id (str): subject id

        Returns:
            BangumiSubject: object containing data for specified subject
        """
        sub_html = self._get_html_for_subject_main(sub_id)
        ep_html = self._get_html_for_subject_eps(sub_id)
        return BangumiSubject.from_html(sub_html, ep_html)

    def get_episode(self, ep_id):
        """Get crucial data for specified episode
        Args:
            ep_id (str): episode id

        Returns:
            BangumiEpisode: object containing data for specified episode
        """
        sub_id = self._get_sub_id_for_ep(ep_id)
        html = self._get_html_for_subject_eps(sub_id)
        return BangumiEpisode.from_html(html, ep_id)

    def get_episodes_for_sub(self, sub_id):
        """Get crucial data for all episodes under specified subject
        Args:
            sub_id (str): subject id

        Returns:
            list of BangumiEpisode: list of objects containing data for
                specified episode
        """
        html = self._get_html_for_subject_eps(sub_id)
        return BangumiEpisode.eps_from_html(html)

    def get_sub_collection(self, sub_id):
        """Get data and collection info for specified subject
        Args:
            sub_id (str): subject id

        Returns:
            BangumiSubjectCollection: containing data and collection info for
                subject. Empty collection with only subject if it's not in
                user's collection
        """
        subject = self.get_subject(sub_id)
        return self.get_sub_collection_with_subject(subject)

    def get_sub_collection_with_subject(self, subject):
        """"Get data collection info for specified subject with provided
        `BangumiSubject` object.

        Args:
            subject (BangumiSubject): subject for which to get collection info

        Returns:
            BangumiSubjectCollection: containing data and collection info for
                subject. Empty collection with only subject if it's not in
                user's collection
        """
        sub_html = self._get_html_for_subject_main(subject.sub_id)
        ep_html = self._get_html_for_subject_eps(subject.sub_id)
        sub_collection = BangumiSubjectCollection.from_html_with_subject(
            subject, sub_html, ep_html)
        sub_collection.set_session(self)
        return sub_collection

    def get_ep_collection(self, ep_id):
        """Get data and collection info for specified episode
        Args:
            ep_id (str): episode id

        Returns:
            BangumiEpisodeCollection: containing data and collection info for
                episode. Empty collection with only episode if it's not in
                user's collection
        """
        episode = self.get_episode(ep_id)
        return self.get_ep_collection_with_episode(episode)

    def get_ep_collection_with_episode(self, episode):
        """Get collection info for given episode
        Args:
            episode (BangumiEpisode): episode for which to get collection info

        Returns:
             BangumiEpisodeCollection: containing data and collection info for
                episode. Empty collection with only episode if it's not in
                user's collection
        """
        sub_id = self._get_sub_id_for_ep(episode.ep_id)
        html = self._get_html_for_subject_eps(sub_id)
        ep_collection = BangumiEpisodeCollection.from_html_with_ep(episode,
                                                                   html)
        ep_collection.set_session(self)
        return ep_collection

    def set_sub_collection(self, sub_coll):
        """Update the collection info on Bangumi according to provided
        BangumiSubjectCollection object

        Note:
             episode collections contained will not be set. Need to explicitly
             call set_ep_collection() or set_n_watched_eps() to set status for
             episode collections.

        Args:
            collection (BangumiSubjectCollection): the object containing data
                to update to Bangumi

        Returns:
            bool: True if successful.
        """
        if not isinstance(sub_coll, BangumiSubjectCollection):
            raise TypeError('Collection must be a BangumiSubjectCollection!' +
                            'Got {0}'.format(type(sub_coll)))
        if sub_coll.c_status not in BangumiSubjectCollection.VALID_C_STATUS:
            raise ValueError('Corrupted c_status value: ' +
                             str(sub_coll.c_status))
        data = {'referer': 'subject', 'interest': sub_coll._c_status,
                'rating': str(sub_coll.rating) if sub_coll.rating else '',
                'tags': ' '.join(sub_coll.tags),
                'comment': sub_coll.comment, 'update': u'保存'}
        set_coll_url = '{0}/subject/{1}/interest/update?gh={2}'.format(
            self.base_url, sub_coll.subject.sub_id, self.gh)
        response = self.session.post(set_coll_url, data)
        return response.status_code == 200

    def set_ep_collection(self, ep_coll):
        if not isinstance(ep_coll, BangumiEpisodeCollection):
            raise TypeError('Collection must be a BangumiEpisodeCollection!' +
                            'Got {0}'.format(type(ep_coll)))
        if ep_coll.c_status not in BangumiEpisodeCollection.VALID_C_STATUS:
            raise ValueError('Corrupted c_status value: ' +
                             str(ep_coll.c_status))
        if ep_coll.c_status == 'watched_till':
            if not ep_coll.sub_collection:
                raise AttributeError("Containing subject collcollection " +
                                     "defined for c_status 'watched_till'")
            else:
                set_url = ('{0}/subject/ep/{1}/status/watched?gh={2}&ajax=1'
                           .format(self.base_url, ep_coll.episode.ep_id,
                                   self.gh))
                data = {'ep_id': ','.join(get_ep_ids_till_this(ep_coll
                                                               .episode))}
                response = self.session.post(set_url, data)
        else:
            set_url = ('{0}/subject/ep/{1}/status/{2}?gh={3}&ajax=1'
                       .format(self.base_url, ep_coll.episode.ep_id,
                               ep_coll.c_status, self.gh))
            response = self.session.get(set_url)
        return response.status_code == 200

    def remove_collection(self, collection):
        if isinstance(collection, BangumiSubjectCollection):
            return self.remove_sub_collection(collection.subject.sub_id)
        elif isinstance(collection, BangumiEpisodeCollection):
            return self.remove_ep_collection(collection.episode.ep_id)
        else:
            raise ValueError("Collection type invalid!")

    def remove_sub_collection(self, sub_id):
        rm_url = '{0}/subject/{1}/remove?gh={2}'.format(self.base_url,
                                                        sub_id, self.gh)
        response = self.session.get(rm_url)
        return response.status_code == 200

    def remove_ep_collection(self, ep_id):
        rm_url = ('{0}/subject/ep/{1}/status/remove?gh={2}'
                  .format(self.base_url, ep_id, self.gh))
        response = self.session.get(rm_url)
        return response.status_code == 200

    def set_n_watched_eps(self, sub_collection):
        """Update number of watched episodes to Bangumi"""
        return self._set_n_watched_eps(sub_collection.subject.sub_id,
                                       sub_collection.n_watched_eps)

    def _set_n_watched_eps(self, sub_id, n_watched_eps):
        set_url = '{0}/subject/set/watched/{1}'.format(self.base_url, sub_id)
        data = {'referer': 'subject', 'submit': u'更新',
                'watchedeps': str(n_watched_eps)}
        response = self.session.post(set_url, data)
        return response.status_code == 200

    def _get_user_id(self):
        response = self.session.get(self.base_url)
        return get_user_id_from_html(response.text)

    def _get_html_for_ep(self, ep_id):
        ep_url = '{0}/ep/{1}'.format(self.base_url, ep_id)
        response = self.session.get(ep_url)
        response.encoding = get_encoding_from_html(response.text)
        return response.text

    def _get_sub_id_for_ep(self, ep_id):
        html = self._get_html_for_ep(ep_id)
        soup = BeautifulSoup(html, 'html.parser')
        sub_id = soup.find(id='subject_inner_info').a['href'].split('/')[-1]
        return sub_id

    def _get_html_for_subject_main(self, sub_id):
        sub_url = '{0}/subject/{1}'.format(self.base_url, sub_id)
        response = self.session.get(sub_url)
        response.encoding = get_encoding_from_html(response.text)
        return response.text

    def _get_html_for_subject_eps(self, sub_id):
        sub_url = '{0}/subject/{1}/ep'.format(self.base_url, sub_id)
        response = self.session.get(sub_url)
        response.encoding = get_encoding_from_html(response.text)
        return response.text

    def _login(self, email, password):
        data = {'email': email, 'password': password,
                'loginsubmit': to_unicode('登录')}
        response = self.session.post(self.base_url + '/FollowTheRabbit', data)
        response.encoding = get_encoding_from_html(response.text)
        if to_unicode('欢迎您回来。现在将转入登录前页面') in response.text:
            self.logged_in = True
        else:
            raise LoginFailedError()

    def _get_gh(self):
        response = self.session.get(self.base_url)
        match_result = re.search(
            '<a href="{0}/logout/(.*?)">'.format(self.base_url),
            response.text)
        return match_result.group(1)
