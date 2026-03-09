"""Tests for motion detection (frames_differ)."""

import numpy as np
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scanner import frames_differ


def make_frame(value: int, shape=(480, 640, 3)) -> np.ndarray:
    """Create a solid-colour BGR frame."""
    return np.full(shape, value, dtype=np.uint8)


def test_none_frames_always_differ():
    assert frames_differ(None, None) is True
    assert frames_differ(None, make_frame(0)) is True
    assert frames_differ(make_frame(0), None) is True


def test_identical_frames_do_not_differ():
    frame = make_frame(128)
    assert frames_differ(frame, frame, threshold=25) is False


def test_identical_copy_does_not_differ():
    frame = make_frame(128)
    assert frames_differ(frame, frame.copy(), threshold=25) is False


def test_large_difference_triggers_motion():
    black = make_frame(0)
    white = make_frame(255)
    assert frames_differ(black, white, threshold=25) is True


def test_small_difference_below_threshold():
    base  = make_frame(100)
    close = make_frame(102)   # delta = 2, well below 25
    assert frames_differ(base, close, threshold=25) is False


def test_small_difference_above_custom_threshold():
    base  = make_frame(100)
    close = make_frame(102)
    assert frames_differ(base, close, threshold=1) is True


def test_noisy_region_triggers_motion():
    """A single bright rectangle in a dark frame should exceed threshold."""
    base  = make_frame(0)
    noisy = make_frame(0)
    noisy[100:200, 100:300] = 200   # bright patch
    assert frames_differ(base, noisy, threshold=25) is True
