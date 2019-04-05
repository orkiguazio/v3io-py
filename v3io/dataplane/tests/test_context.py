import os
import unittest

import future.utils

import v3io.common.helpers
import v3io.dataplane
import v3io.logger


class TextContext(unittest.TestCase):

    def setUp(self):
        self._logger = logger = v3io.logger.Client('test', v3io.logger.Severity.Debug).logger
        self._context = v3io.dataplane.Context(logger, [os.environ['V3IO_DATAPLANE_URL']])
        self._access_key = os.environ['V3IO_DATAPLANE_ACCESS_KEY']
        self._container_name = 'bigdata'
        self._path = 'emd0'

    def test_emd(self):
        items = {
            'bob': {'age': 42, 'feature': 'mustache'},
            'linda': {'age': 41, 'feature': 'singing'},
            'louise': {'age': 9, 'feature': 'bunny ears'},
            'tina': {'age': 14, 'feature': 'butts'},
        }

        for item_key, item_attributes in future.utils.viewitems(items):
            response = self._context.put_item(self._container_name,
                                              self._access_key,
                                              v3io.common.helpers.url_join(self._path, item_key),
                                              item_attributes)

            response.raise_for_status()

        self._verify_items(self._path, items)

        response = self._context.update_item(self._container_name,
                                             self._access_key,
                                             v3io.common.helpers.url_join(self._path, 'louise'),
                                             {
                                                 'height': 130,
                                                 'quip': 'i can smell fear on you'
                                             })

        response.raise_for_status()

        response = self._context.get_item(self._container_name,
                                          self._access_key,
                                          v3io.common.helpers.url_join(self._path, 'louise'),
                                          attribute_names=['__size', 'age', 'quip', 'height'])

        response.raise_for_status()

        self.assertEqual(0, response.item['__size'])
        self.assertEqual(9, response.item['age'])
        self.assertEqual('i can smell fear on you', response.item['quip'])
        self.assertEqual(130, response.item['height'])

        items = v3io.dataplane.ItemsCursor(self._context,
                                           self._container_name,
                                           self._access_key,
                                           self._path + '/',
                                           attribute_names=['age', 'feature'],
                                           filter_expression='age > 15').all()

        self.assertEqual(2, len(items))
        for item in items:
            self.assertLess(15, item['age'])

        #
        # Increment age
        #

        response = self._context.update_item(self._container_name,
                                             self._access_key,
                                             v3io.common.helpers.url_join(self._path, 'louise'),
                                             expression='age = age + 1')

        response.raise_for_status()

        response = self._context.get_item(self._container_name,
                                          self._access_key,
                                          v3io.common.helpers.url_join(self._path, 'louise'),
                                          attribute_names=['age'])

        response.raise_for_status()

        self.assertEqual(10, response.item['age'])

    def test_put_items(self):
        items = {
            'bob': {'age': 42, 'feature': 'mustache'},
            'linda': {'age': 42, 'feature': 'singing'}
        }

        response = self._context.put_items(self._container_name,
                                           self._access_key,
                                           '/emd0',
                                           items)

        self.assertTrue(response.success)

        self._verify_items('/emd0', items)

    def _verify_items(self, path, items):
        items_cursor = v3io.dataplane.ItemsCursor(self._context,
                                                  self._container_name,
                                                  self._access_key,
                                                  path + '/',
                                                  attribute_names=['*'])

        received_items = items_cursor.all()

        # TODO: verify contents
        self.assertEqual(len(items), len(received_items))
