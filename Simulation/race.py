class RaceCar:
    def __init__(self,name,color,lap_duration,total_laps=3,pit_after_lap=1,pit_duration=3.0):
        self.name = name
        self.color = color
        self.lap_duration = lap_duration
        self.total_laps = total_laps

        self.pit_after_lap = pit_after_lap
        self.pit_duration = pit_duration

        self.elapsed = 0.0
        self.progress = 0.0
        self.laps_completed = 0
        self.finished = False
        self.status = "RACING"

    def update(self, dt):
        if self.finished:
            return

        pit_start = self.pit_after_lap * self.lap_duration
        pit_end = pit_start + self.pit_duration

        race_duration = (
            self.lap_duration * self.total_laps
            + self.pit_duration
        )

        self.elapsed = min(
            self.elapsed + dt,
            race_duration
        )

        if self.elapsed < pit_start:
            driving_elapsed = self.elapsed
            self.status = "RACING"

        elif self.elapsed < pit_end:
            driving_elapsed = pit_start
            self.status = "PIT"

        else:
            driving_elapsed = self.elapsed - self.pit_duration
            self.status = "RACING"

        completed = driving_elapsed / self.lap_duration

        self.laps_completed = min(
            self.total_laps,
            int(completed)
        )

        self.progress = completed % 1.0
        self.finished = self.elapsed >= race_duration

        if self.finished:
            self.status = "FINISHED"

def demo_lap_time(compound, tyre_age, race_lap, total_laps):
    base_times = {
        "Soft": 9.0,
        "Medium": 10.0,
        "Hard": 11.0,
    }

    degradation = 0.5 * (tyre_age - 1)

    return base_times[compound] + degradation

#Cuoc dua chinh
def build_timeline(strategy, lap_time_fn, pit_duration=3.0):
    timeline = []

    current_time = 0.0
    race_lap = 1
    total_laps = sum(length for _, length in strategy)

    for stint_index, (compound, length) in enumerate(strategy):
        for tyre_age in range(1, length + 1):
            duration = lap_time_fn(
                compound=compound,
                tyre_age=tyre_age,
                race_lap=race_lap,
                total_laps=total_laps
            )

            timeline.append({
                "status": "RACING",
                "lap": race_lap,
                "compound": compound,
                "tyre_age": tyre_age,
                "start": current_time,
                "end": current_time + duration,
            })

            current_time += duration
            race_lap += 1

        # Thêm pit giữa hai stint, không thêm sau stint cuối
        if stint_index < len(strategy) - 1:
            timeline.append({
                "status": "PIT",
                "lap": race_lap - 1,
                "compound": compound,
                "tyre_age": length,
                "start": current_time,
                "end": current_time + pit_duration,
            })

            current_time += pit_duration

    return timeline