#!/usr/bin/python
"""This module contains classes for unit testing etl_demo ComputeManager class.
"""



import os
import unittest

import gflags as flags
from apiclient.errors import HttpError
from mock import MagicMock
from mock import patch
from mock import PropertyMock

import etl_demo

FLAGS = flags.FLAGS


class ComputeManagerTest(unittest.TestCase):

  def setUp(self):
    self.manager = etl_demo.ComputeManager()

  def tearDown(self):
    patch.stopall()

  def testStartInstance_created(self):
    mock_api = MagicMock(name='Mock API')
    self.manager.GetApi = MagicMock(return_value=mock_api)
    mock_builtin_open = patch('__builtin__.open').start()
    property_mock = PropertyMock(side_effect=HttpError(
        'resp', 'content'))
    mock_api.GetInstance = property_mock

    self.assertTrue(self.manager.StartInstance())
    mock_api.GetInstance.assert_called_once_with('myinstance')
    self.assertTrue(mock_api.CreateInstance.called)
    self.assertTrue(mock_builtin_open.called)

  def testStartInstance_notCreated(self):
    mock_api = MagicMock(name='Mock API')
    self.manager.GetApi = MagicMock(return_value=mock_api)
    mock_api.GetInstance.return_value = True

    self.assertTrue(self.manager.StartInstance())
    mock_api.GetInstance.assert_called_once_with('myinstance')
    self.assertFalse(mock_api.CreateInstance.called)


if __name__ == '__main__':
  unittest.main()
