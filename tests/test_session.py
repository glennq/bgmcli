# -*- coding: utf-8 -*-
import unittest
from bgmcli.api import BangumiSession


class BangumiSessionTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls._session = BangumiSession('glennqjy@gmail.com', '15263748')
        sub_coll = cls._session.get_sub_collection("265")
        cls.set_up_sub_coll(sub_coll)
        if sub_coll.sync_collection() and sub_coll.sync_n_watched_eps():
            sub_coll.ep_collections[-1].c_status = 'queue'
            sub_coll.ep_collections[-1].sync_collection()
            sub_coll.ep_collections[-2].c_status = 'drop'
            sub_coll.ep_collections[-2].sync_collection()
            cls._sub_coll = sub_coll
        else:
            cls.fail("setup failed")
        
    @classmethod
    def tearDownClass(cls):
        cls._sub_coll.remove_with_sync()
        cls._session.logout()
    
    @staticmethod 
    def set_up_sub_coll(sub_coll):
        sub_coll.c_status = 3
        sub_coll.comment = u'佳作'
        sub_coll.tags = [u'科幻', u'TV']
        sub_coll.rating = 8
        sub_coll.n_watched_eps = 26

    def test_constructor_exception(self):
        with self.assertRaises(ValueError):
            BangumiSession('glennqjy@gmail.com', '15263748', 'abc.com')

    def test_get_subject_anime(self):
        subject = self._session.get_subject("253")
        self.assertEqual("253", subject.id_)
        self.assertEqual(u'カウボーイビバップ', subject.title)
        self.assertEqual(u'星际牛仔', subject.ch_title)
        self.assertEqual(26, subject.n_eps)
        for ep in subject.eps:
            self.assertIs(subject, ep.subject)
        
    def test_get_subject_other(self):
        with self.assertRaises(NotImplementedError):
            self._session.get_subject('7250')
        with self.assertRaises(NotImplementedError):
            self._session.get_subject('36752')
        with self.assertRaises(NotImplementedError):
            self._session.get_subject('49561')
            
    def test_get_episode(self):
        ep = self._session.get_episode("7028")
        self.assertEqual("7028", ep.id_)
        self.assertEqual(u'ホンキィ・トンク・ウィメン', ep.title)
        self.assertEqual(u'Honky Tonk Women', ep.ch_title)
        self.assertEqual(3, ep.ep_num)
        self.assertEqual('EP', ep.ep_type)
        self.assertEqual('air', ep.status)
        
    def test_get_episodes_for_sub(self):
        eps = self._session.get_episodes_for_sub("253")
        self.assertEqual(31, len(eps))
        ep_ids = [519] + range(7027, 7052) + [46037] + range(103232, 103236)
        ep_ids = [str(i) for i in ep_ids]
        ep_nums = range(1, 27) + [0, 1, 1, 2, 3]
        ep_types = ['EP'] * 26 + ['SP', 'OP'] + ['ED'] * 3
        for ep, ep_id, ep_num, ep_type in zip(eps, ep_ids, ep_nums, ep_types):
            self.assertEqual(ep_id, ep.id_)
            self.assertEqual(ep_num, ep.ep_num)
            self.assertEqual(ep_type, ep.ep_type)

    def test_get_ep_collection(self):
        ep_coll = self._session.get_ep_collection("1078")
        self.assertEqual('queue', ep_coll.c_status)
        self.assertIs(self._session, ep_coll.session)
        
    def test_get_ep_collection_with_episode(self):
        ep = self._session.get_episode("1077")
        ep_coll = self._session.get_ep_collection_with_episode(ep)
        self.assertEqual('drop', ep_coll.c_status)
        self.assertIs(self._session, ep_coll.session)
        
    def test_get_sub_collection_anime(self):
        sub_coll = self._session.get_sub_collection("265")
        self.assertIs(self._session, sub_coll.session)
        self.assertEqual(self._sub_coll, sub_coll)
        for ep_coll1, ep_coll2 in zip(sub_coll.ep_collections,
                                      self._sub_coll.ep_collections):
            self.assertIs(sub_coll, ep_coll1.sub_collection)
            self.assertIs(self._session, ep_coll1.session)
            self.assertEqual(ep_coll2, ep_coll1)
        
    def test_get_sub_collection_other(self):
        with self.assertRaises(NotImplementedError):
            self._session.get_sub_collection('7250')
        with self.assertRaises(NotImplementedError):
            self._session.get_sub_collection('36752')
        with self.assertRaises(NotImplementedError):
            self._session.get_sub_collection('49561')
            
    def test_get_sub_collection_with_subject_anime(self):
        subject = self._session.get_subject("265")
        sub_coll = self._session.get_sub_collection_with_subject(subject)
        self.assertIs(self._session, sub_coll.session)
        self.assertEqual(self._sub_coll, sub_coll)
        for ep_coll1, ep_coll2 in zip(sub_coll.ep_collections,
                                      self._sub_coll.ep_collections):
            self.assertIs(sub_coll, ep_coll1.sub_collection)
            self.assertIs(self._session, ep_coll1.session)
            self.assertEqual(ep_coll2, ep_coll1)
            
    def test_set_collection_exception(self):
        with self.assertRaises(TypeError):
            self._session.set_collection(self._session)
    
    def test_set_sub_collection(self):
        with self.assertRaises(TypeError):
            self._session.set_sub_collection(self._session)
        sub_coll = self._session.get_sub_collection("253")
        if sub_coll.c_status:
            sub_coll.remove_with_sync()
        with self.assertRaises(AttributeError):
            self._session.set_sub_collection(sub_coll)
        with self.assertRaises(ValueError):
            sub_coll._c_status = 6
            self._session.set_sub_collection(sub_coll)
        sub_coll.c_status = 3
        sub_coll.sync_collection()
        new_sub_coll = self._session.get_sub_collection("253")
        self.assertEqual(sub_coll.c_status, new_sub_coll.c_status)
        
    def test_set_ep_collection(self):
        with self.assertRaises(TypeError):
            self._session.set_ep_collection(self._session)
        sub_coll = self._session.get_sub_collection("253")
        if sub_coll.c_status != 3:
            sub_coll.c_status = 3
            sub_coll.sync_collection()
        ep_coll = sub_coll.ep_collections[0]
        if ep_coll.c_status:
            ep_coll.remove_with_sync()
        with self.assertRaises(AttributeError):
            self._session.set_ep_collection(ep_coll)
        with self.assertRaises(ValueError):
            ep_coll._c_status = 'invalid'
            self._session.set_ep_collection(ep_coll)
        ep_coll.c_status = 'watched'
        ep_coll.sync_collection()
        new_ep_coll = self._session.get_ep_collection(ep_coll.episode.id_)
        self.assertEqual(ep_coll.c_status, new_ep_coll.c_status)
        
    def test_set_ep_collection_watched_up_to(self):
        sub_coll = self._session.get_sub_collection("253")
        if sub_coll.c_status != 3:
            sub_coll.c_status = 3
            sub_coll.sync_collection()
        up_to = 6
        ep_coll = sub_coll.ep_collections[up_to]
        ep_coll.remove_with_sync()
        ep_coll.c_status = 'watched_up_to'

        with self.assertRaises(AttributeError):
            ep_coll._sub_collection = None
            self._session.set_ep_collection(ep_coll)
        
        ep_coll.sub_collection = sub_coll
        self.assertTrue(self._session.set_ep_collection(ep_coll))
        for i in range(up_to + 1):
            self.assertEqual('watched', sub_coll.ep_collections[i].c_status)
        
    def test_remove_collection_exception(self):
        with self.assertRaises(TypeError):
            self._session.remove_collection(self._session)
    
    def test_set_n_watched_eps(self):
        sub_coll = self._session.get_sub_collection("253")
        if sub_coll.c_status != 1:
            sub_coll.c_status = 1
            self._session.set_sub_collection(sub_coll)
        with self.assertRaises(ValueError):
            self._session.set_n_watched_eps(sub_coll)

        sub_coll.c_status = 3
        self._session.set_sub_collection(sub_coll)
        sub_coll._n_watched_eps = None
        with self.assertRaises(AttributeError):
            self._session.set_n_watched_eps(sub_coll)
        
        sub_coll._n_watched_eps = 26
        self._session.set_n_watched_eps(sub_coll)
        new_sub_coll = self._session.get_sub_collection("253")
        self.assertEqual(26, new_sub_coll.n_watched_eps)
        
    def test_get_dummy_collections(self):
        with self.assertRaises(ValueError):
            self._session.get_dummy_collections('invalid', 3)
        with self.assertRaises(ValueError):
            self._session.get_dummy_collections('anime', 6)
        dummy_colls = self._session.get_dummy_collections('anime', 4)
        sub_ids = [coll.subject.id_ for coll in dummy_colls]
        titles = [coll.subject.title for coll in dummy_colls]
        ch_titles = [coll.subject.ch_title for coll in dummy_colls]
        c_statuses = [coll.c_status for coll in dummy_colls]
        ratings = [coll.rating for coll in dummy_colls]
        self.assertEqual(['1451', '45241', '8484'], sub_ids)
        self.assertEqual([u'東のエデン', u'ベルセルク  黄金時代篇III 降臨',
                          u'機動警察パトレイバー'], titles)
        self.assertEqual([u'东之伊甸', u'剑风传奇 黄金时代篇III 降临', u'机动警察'],
                         ch_titles)
        self.assertEqual([4, 4, 4], c_statuses)
        self.assertEqual([6, 6, 7], ratings)
            