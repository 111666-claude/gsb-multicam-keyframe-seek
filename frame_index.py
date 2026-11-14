"""Index for switching among live match camera angles."""


class FrameIndex:
    def __init__(self):
        self.frames = []
        self.Work = 0

    def apply(self, event):
        if event["op"] == "frame":
            self.frames.append(dict(event))
        elif event["op"] == "restart":
            pass
        else:
            raise ValueError("unknown event")

    def seek(self, angle, target, max_age):
        selected = None
        for frame in self.frames:
            self.Work += 1
            if frame["angle"] != angle:
                continue
            if abs(frame["pts"] - target) <= max_age:
                if selected is None or abs(frame["pts"] - target) < abs(selected["pts"] - target):
                    selected = frame
        return None if selected is None else (selected["pts"], selected["seq"])
