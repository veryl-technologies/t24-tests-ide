#  Copyright 2008-2012 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os

from robot.parsing.model import TestCaseFile, TestDataDirectory


def NewTestCaseFile(path):
    datafile = TestCaseFile(source=path)
    datafile.setting_table.add_library('T24WebDriver.py')  # Rely that we have it setup in PYTHONPATH
    datafile.setting_table.add_library('Selenium2Library')
    datafile.setting_table.suite_teardown.name = 'Close Browsers'  # or maybe test_teardown ?

    _create_missing_directories(datafile.directory)
    return datafile


def NewTestDataDirectory(path):
    dirname = os.path.dirname(path)
    datafile = TestDataDirectory(source=dirname)
    datafile.initfile = path
    _create_missing_directories(dirname)
    return datafile


def _create_missing_directories(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
