# Multi-camera seek

Live match cameras send frame records with `angle`, `epoch`, `pts`, `seq`, and
`keyframe`. A `restart` event for one angle advances its epoch and invalidates
older frames for that angle. Repeated `seq` values in the current epoch are
idempotent. A viewer switching to an angle needs the latest **keyframe** at or
before the target PTS, within `max_age`. A future frame cannot serve a past
seek. No result is returned when the current epoch has no eligible keyframe.

The index must support long-running streams. `Work` counts frame candidates
examined by seeks; seeking a recent point cannot linearly rescan archived
frames from other epochs or angles.
