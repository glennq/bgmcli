# -*- coding: utf-8 -*-
import os
import unittest
from bgmcli.api import BangumiSession
from bgmcli.api.element import BangumiEpisode, BangumiAnime
from bgmcli.api.collection import BangumiAnimeCollection,\
    BangumiEpisodeCollection
from test_utils import module_path
    

class BangumiEpisodeCollectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.split(module_path(cls.setUpClass))[0]
        ep_html_path = os.path.join(path, 'ep_html')
        sub_html_path = os.path.join(path, 'sub_html')
        with open(ep_html_path) as f:
            cls._ep_html = f.read()
        with open(sub_html_path) as f:
            cls._sub_html = f.read()
        cls._c_statuses = ['watched'] * 24 + ['queue', 'drop'] + [None] * 5
        cls._sub_id = "253"
        
    def test_from_html(self):
        ep_id = "519"
        ep_coll = BangumiEpisodeCollection.from_html(ep_id, self._ep_html)
        self.assertEqual(self._c_statuses[0], ep_coll.c_status)
        
    def test_from_html_with_ep(self):
        ep_id = "519"
        ep = BangumiEpisode.from_html(ep_id, self._ep_html)
        ep_coll = BangumiEpisodeCollection.from_html_with_ep(ep,
                                                             self._ep_html)
        self.assertEqual(self._c_statuses[0], ep_coll.c_status)
        
    def test_ep_colls_for_sub_from_html(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        ep_colls = (BangumiEpisodeCollection
                    .ep_colls_for_sub_from_html(sub, self._ep_html))
        c_statuses = [ep_coll.c_status for ep_coll in ep_colls]
        for c_status, c_status_expected in zip(c_statuses, self._c_statuses):
            self.assertEqual(c_status_expected, c_status)
            
    def test_from_to_json(self):
        ep_id = "519"
        ep_coll = BangumiEpisodeCollection.from_html(ep_id, self._ep_html)
        json_text = ep_coll.to_json()
        ep_coll_new = BangumiEpisodeCollection.from_json(json_text)
        self.assertEqual(ep_coll, ep_coll_new)
        
    def test_c_status(self):
        ep_id = "519"
        ep_coll = BangumiEpisodeCollection.from_html(ep_id, self._ep_html)
        with self.assertRaises(ValueError):
            ep_coll.c_status = 'invalid'
        self.assertEqual('watched', ep_coll.c_status)
        ep_coll.c_status = 'drop'
        self.assertEqual('drop', ep_coll.c_status)
        
    def test_sub_collection(self):
        ep_id = "519"
        ep_coll = BangumiEpisodeCollection.from_html(ep_id, self._ep_html)
        self.assertIsNone(ep_coll.sub_collection)
        with self.assertRaises(TypeError):
            ep_coll.sub_collection = ep_coll
            

class BangumiAnimeCollectionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.path.split(module_path(cls.setUpClass))[0]
        ep_html_path = os.path.join(path, 'ep_html')
        sub_html_path = os.path.join(path, 'sub_html')
        with open(ep_html_path) as f:
            cls._ep_html = f.read()
        with open(sub_html_path) as f:
            cls._sub_html = f.read()
        cls._c_status = 3
        cls._sub_id = "253"
        cls._rating = 8
        cls._tags = [u'科幻', u'TV', u'SUNRISE']
        cls._comment = u'佳作'
        cls._n_watched_eps = 25
        
    def test_from_html(self):
        sub_coll = BangumiAnimeCollection.from_html(self._sub_html,
                                                    self._ep_html)
        for name in ['_c_status', '_rating', '_tags', '_comment',
                     '_n_watched_eps']:
            self.assertEqual(getattr(self, name), getattr(sub_coll, name))
            
    def test_from_html_with_subject(self):
        sub = BangumiAnime.from_html(self._sub_html, self._ep_html)
        sub_coll = (BangumiAnimeCollection
                    .from_html_with_subject(sub, self._sub_html,
                                            self._ep_html))
        for name in ['_c_status', '_rating', '_tags', '_comment',
                     '_n_watched_eps']:
            self.assertEqual(getattr(self, name), getattr(sub_coll, name))
            
    def test_from_to_json(self):
        sub_coll = BangumiAnimeCollection.from_html(self._sub_html,
                                                    self._ep_html)
        json_text = sub_coll.to_json()
        sub_coll_new = BangumiAnimeCollection.from_json(json_text)
        self.assertEqual(sub_coll, sub_coll_new)
        
    def test_n_watched_eps(self):
        sub_coll = BangumiAnimeCollection.from_html(self._sub_html,
                                                    self._ep_html)
        with self.assertRaises(ValueError):
            sub_coll.n_watched_eps = -1
        with self.assertRaises(ValueError):
            sub_coll.n_watched_eps = sub_coll.subject.n_eps + 1
            
    def test_ep_collections(self):
        sub_coll = BangumiAnimeCollection.from_html(self._sub_html,
                                                    self._ep_html)
        with self.assertRaises(TypeError):
            sub_coll.ep_collections = [sub_coll]
            
    def test_find_ep_coll(self):
        sub_coll = BangumiAnimeCollection.from_html(self._sub_html,
                                                    self._ep_html)
        self.assertEqual(sub_coll.ep_collections[0],
                         sub_coll.find_ep_coll("519"))
        self.assertEqual(sub_coll.ep_collections[-1],
                         sub_coll.find_ep_coll("ED3"))
        self.assertIsNone(sub_coll.find_ep_coll("ED5"))
        
    def test_watched_up_to_with_sync(self):
        with BangumiSession('glennqjy@gmail.com', '15263748') as session:
            sub_coll = session.get_sub_collection("265")
            self.set_up_sub_coll(sub_coll)
            if sub_coll.sync_collection() and sub_coll.sync_n_watched_eps():
                sub_coll.ep_collections[0].c_status = 'queue'
                sub_coll.ep_collections[0].sync_collection()
                sub_coll.ep_collections[1].remove_with_sync()
            else:
                self.fail()
            
            self.assertEqual('queue', sub_coll.ep_collections[0].c_status)
            self.assertEqual(None, sub_coll.ep_collections[1].c_status)
            with self.assertRaises(ValueError):
                ep_id = "519"
                ep_coll = BangumiEpisodeCollection.from_html(ep_id,
                                                             self._ep_html)
                sub_coll.watched_up_to_with_sync(ep_coll)
            with self.assertRaises(ValueError):
                sub_coll.watched_up_to_with_sync("SP10")
            with self.assertRaises(TypeError):
                sub_coll.watched_up_to_with_sync(sub_coll)
                
            sub_coll.watched_up_to_with_sync("EP2")
            for i in range(2):
                self.assertEqual('watched',
                                 sub_coll.ep_collections[i].c_status)
                
    def set_up_sub_coll(self, sub_coll):
        sub_coll.c_status = 3
        sub_coll.comment = u'佳作'
        sub_coll.tags = [u'科幻', u'TV']
        sub_coll.rating = 8
        sub_coll.n_watched_eps = 26
                         
            
        