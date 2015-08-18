# -*- coding: utf-8 -*-
import unittest
import os
from bgmcli.api import BangumiSession
from bgmcli.api.element import BangumiAnime, BangumiEpisode, FixedAttribute
from test_utils import module_path


class BangumiEpisodeTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        path = os.path.split(module_path(cls.setUpClass))[0]
        ep_html_path = os.path.join(path, 'ep_html')
        with open(ep_html_path) as f:
            cls._ep_html = f.read()
        ep_ids = [519] + range(7027, 7052) + [46037] + range(103232, 103236)
        cls._ep_ids = [str(i) for i in ep_ids]
        cls._ep_nums = range(1, 27) + [0, 1, 1, 2, 3]
        cls._ep_types = ['EP'] * 26 + ['SP', 'OP'] + ['ED'] * 3

    def test_from_html(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        self.assertEqual(self._ep_ids[0], ep.ep_id)
        self.assertEqual(self._ep_nums[0], ep.ep_num)
        self.assertEqual(self._ep_types[0], ep.ep_type)
        
    def test_eps_from_html(self):
        eps = BangumiEpisode.eps_from_html(self._ep_html)
        self.assertEqual(31, len(eps))
        for ep, ep_id, ep_num, ep_type in zip(eps, self._ep_ids,
                                              self._ep_nums, self._ep_types):
            self.assertEqual(ep_id, ep.ep_id)
            self.assertEqual(ep_num, ep.ep_num)
            self.assertEqual(ep_type, ep.ep_type)
            
    def test_from_to_json(self):
        eps = BangumiEpisode.eps_from_html(self._ep_html)
        ep_jsons = [ep.to_json() for ep in eps]
        eps_new = [BangumiEpisode.from_json(ep_json) for ep_json in ep_jsons]
        for ep, ep_new in zip(eps, eps_new):
            self.assertEqual(ep, ep_new)
            
    def test_fix_attribute_exception(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        for key, value in BangumiEpisode.__dict__.items():
            if isinstance(value, FixedAttribute) and getattr(ep, '_' + key):
                with self.assertRaises(AttributeError):
                    setattr(ep, key, 's')
                    
    def test_fix_attribute_success(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        ep._ep_id = None
        self.assertIsNone(ep.ep_id)
        ep.ep_id = ep_id
        self.assertEqual(ep_id, ep.ep_id)
        
    def test_status(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        with self.assertRaises(ValueError):
            ep.status = 'invalid'
        self.assertEqual('air', ep.status)
        ep.status = 'na'
        self.assertEqual('na', ep.status)
        ep.status = 'today'
        self.assertEqual('today', ep.status)
        
    def test_subject(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        self.assertIsNone(ep.subject)
        with self.assertRaises(TypeError):
            ep.subject = ep
            
    def test_to_collection(self):
        with BangumiSession('glennqjy@gmail.com', '15263748') as session:
            ep = session.get_episode("519")
            ep_coll = session.get_ep_collection("519")
            ep_coll_other = ep.to_collection(session)
            self.assertEqual(ep_coll, ep_coll_other)
            self.assertIs(session, ep_coll_other.session)
        

class BangumiAnimeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.split(module_path(cls.setUpClass))[0]
        ep_html_path = os.path.join(path, 'ep_html')
        sub_html_path = os.path.join(path, 'sub_html')
        with open(ep_html_path) as f:
            cls._ep_html = f.read()
        with open(sub_html_path) as f:
            cls._sub_html = f.read()
        cls._sub_id = "253"
        cls._title = u'カウボーイビバップ'
        cls._ch_title = u'星际牛仔'
        cls._n_eps = 26
        
    def test_from_html(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        for attr_name in ['_sub_id', '_title', '_ch_title', '_n_eps']:
            self.assertEqual(getattr(self, attr_name),
                             getattr(sub, attr_name))
            
    def test_from_to_json(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        json_text = sub.to_json()
        new_sub = BangumiAnime.from_json(json_text)
        self.assertEqual(sub, new_sub)
        for ep, new_ep in zip(sub.eps, new_sub.eps):
            self.assertEqual(ep, new_ep)
            
    def test_n_eps(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        with self.assertRaises(ValueError):
            sub.n_eps = -1
        with self.assertRaises(ValueError):
            sub.n_eps = 'abc'
        self.assertEqual(self._n_eps, sub.n_eps)
        sub.n_eps = 10
        self.assertEqual(10, sub.n_eps)
        
    def test_eps(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        with self.assertRaises(TypeError):
            sub.eps = [sub]
        self.assertEqual(31, len(sub.eps))
        sub.eps = sub.eps[:26]
        self.assertEqual(26, len(sub.eps))
        
    def test_to_collection(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        with BangumiSession('glennqjy@gmail.com', '15263748') as session:
            sub_coll = sub.to_collection(session)
            sub_coll_other = session.get_sub_collection(self._sub_id)
            self.assertIs(session, sub_coll.session)
            self.assertEqual(sub_coll, sub_coll_other)