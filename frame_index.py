"""Index for switching among live match camera angles."""

from bisect import bisect_right


class _AngleState:
    """Per-angle index. Frames from older epochs are dropped on restart."""

    __slots__ = ("epoch", "seqs", "key_pts", "key_frames")

    def __init__(self, epoch):
        self.epoch = epoch
        self.seqs = set()        # seq values seen in the current epoch
        self.key_pts = []        # sorted PTS of keyframes (current epoch only)
        self.key_frames = []     # frame dicts parallel to key_pts

    def reset(self, epoch):
        self.epoch = epoch
        self.seqs.clear()
        self.key_pts.clear()
        self.key_frames.clear()


class FrameIndex:
    def __init__(self):
        self._angles = {}
        self.Work = 0

    def apply(self, event):
        op = event["op"]
        if op == "frame":
            self._apply_frame(event)
        elif op == "restart":
            angle = event["angle"]
            state = self._angles.get(angle)
            epoch = event.get("epoch")
            if state is None:
                self._angles[angle] = _AngleState(epoch if epoch is not None else 0)
            elif epoch is None or epoch > state.epoch:
                state.reset(epoch if epoch is not None else state.epoch + 1)
        else:
            raise ValueError("unknown event")

    def _apply_frame(self, event):
        angle = event["angle"]
        epoch = event["epoch"]
        state = self._angles.get(angle)
        if state is None:
            state = self._angles[angle] = _AngleState(epoch)
        if epoch < state.epoch:
            return  # stale frame from a dead epoch
        if epoch > state.epoch:
            state.reset(epoch)  # stream advanced without an explicit restart
        seq = event["seq"]
        if seq in state.seqs:
            return  # repeated seq in the current epoch is idempotent
        state.seqs.add(seq)
        if event["keyframe"]:
            frame = {"pts": event["pts"], "seq": seq}
            idx = bisect_right(state.key_pts, frame["pts"])
            state.key_pts.insert(idx, frame["pts"])
            state.key_frames.insert(idx, frame)

    def seek(self, angle, target, max_age):
        state = self._angles.get(angle)
        if state is None:
            return None
        # Latest keyframe at or before the target; a future frame can never
        # serve a past seek, and only keyframes are candidates.
        idx = bisect_right(state.key_pts, target) - 1
        if idx < 0:
            return None
        frame = state.key_frames[idx]
        self.Work += 1
        if target - frame["pts"] > max_age:
            return None
        return (frame["pts"], frame["seq"])
