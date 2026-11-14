import unittest

from frame_index import FrameIndex


class FrameIndexBasicTests(unittest.TestCase):
    def test_exact_keyframe(self):
        index = FrameIndex()
        index.apply({"op": "frame", "angle": "main", "epoch": 1, "pts": 100, "seq": 1, "keyframe": True})
        self.assertEqual(index.seek("main", 100, 20), (100, 1))


if __name__ == "__main__":
    unittest.main()
