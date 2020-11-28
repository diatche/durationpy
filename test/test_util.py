import os
import sys
import pytest
from durationpy import util

module_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(module_dir, '..', 'durationpy'))


def test_flatten():
    assert util.flatten([[1], [2, [3]]]) == [1, 2, 3]
    assert util.flatten([[1]]) == [1]
    assert util.flatten([1]) == [1]
    assert util.flatten(1) == [1]
    assert util.flatten([['foo']]) == ['foo']
    assert util.flatten(['foo']) == ['foo']
    assert util.flatten('foo') == ['foo']
    assert util.flatten([[{ 'foo': 'bar' }]]) == [{ 'foo': 'bar' }]
    assert util.flatten([{ 'foo': 'bar' }]) == [{ 'foo': 'bar' }]
    assert util.flatten({ 'foo': 'bar' }) == [{ 'foo': 'bar' }]
