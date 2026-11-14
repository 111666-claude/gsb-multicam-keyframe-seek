import unittest

from frame_index import FrameIndex


def frame(angle, epoch, pts, seq, keyframe):
    return {"op": "frame", "angle": angle, "epoch": epoch, "pts": pts, "seq": seq, "keyframe": keyframe}


class FrameIndexBasicTests(unittest.TestCase):
    def test_exact_keyframe(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 100, 1, True))
        self.assertEqual(index.seek("main", 100, 20), (100, 1))

    def test_past_keyframe_beats_future_one(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 90, 1, True))
        index.apply(frame("main", 1, 105, 2, True))
        self.assertEqual(index.seek("main", 100, 20), (90, 1))

    def test_non_keyframe_is_not_a_candidate(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 80, 1, True))
        index.apply(frame("main", 1, 99, 2, False))
        self.assertEqual(index.seek("main", 100, 30), (80, 1))

    def test_future_only_gives_no_result(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 105, 1, True))
        self.assertIsNone(index.seek("main", 100, 20))

    def test_beyond_max_age_gives_no_result(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 10, 1, True))
        self.assertIsNone(index.seek("main", 100, 20))

    def test_restart_invalidates_old_epoch(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 90, 1, True))
        index.apply({"op": "restart", "angle": "main", "epoch": 2})
        self.assertIsNone(index.seek("main", 100, 50))
        index.apply(frame("main", 2, 95, 1, True))
        self.assertEqual(index.seek("main", 100, 50), (95, 1))

    def test_stale_epoch_frame_ignored(self):
        index = FrameIndex()
        index.apply({"op": "restart", "angle": "main", "epoch": 2})
        index.apply(frame("main", 2, 95, 5, True))
        index.apply(frame("main", 1, 99, 9, True))  # late frame from dead epoch
        self.assertEqual(index.seek("main", 100, 50), (95, 5))

    def test_duplicate_seq_is_idempotent(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 90, 1, True))
        index.apply(frame("main", 1, 95, 1, True))  # same seq, must not add a candidate
        self.assertEqual(index.seek("main", 100, 50), (90, 1))

    def test_angles_are_isolated(self):
        index = FrameIndex()
        index.apply(frame("main", 1, 90, 1, True))
        index.apply(frame("side", 1, 95, 1, True))
        index.apply({"op": "restart", "angle": "side", "epoch": 2})
        self.assertEqual(index.seek("main", 100, 50), (90, 1))
        self.assertIsNone(index.seek("side", 100, 50))

    def test_unknown_angle_gives_no_result(self):
        index = FrameIndex()
        self.assertIsNone(index.seek("nope", 100, 50))

    def test_seek_work_is_bounded(self):
        index = FrameIndex()
        for i in range(3000):
            angle = "main" if i % 2 == 0 else "side"
            index.apply(frame(angle, 1, i, i, i % 10 == 0))
        for i in range(200):
            self.assertIsNotNone(index.seek("main", 2900 + i % 100, 500))
        self.assertLessEqual(index.Work, 6000)


if __name__ == "__main__":
    unittest.main()
