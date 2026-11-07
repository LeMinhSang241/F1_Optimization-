import json
import math
import random
import sys
from pathlib import Path

# Thư mục gốc để đọc bảng cấu hình và file hệ số lốp.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from data.race_configs import DIRTY_AIR_PARAMS, RACE_CONFIGS, SC_PARAMS

# Nhiệt độ chuẩn của từng chặng. Đúng nhiệt này thì hệ số mòn không bị chỉnh.
REFERENCE_TRACK_TEMPERATURE = {
    "monza": 30.0,
    "silverstone": 28.0,
}

# Độ nhạy nhiệt của từng loại lốp, cùng quy tắc với mô hình Pirelli.
THERMAL_WEAR = {
    "Soft": {"linear_sensitivity": 0.30, "quadratic_sensitivity": 1.80, "heat_spike": 1.20},
    "Medium": {"linear_sensitivity": 0.25, "quadratic_sensitivity": 1.20, "heat_spike": 0.80},
    "Hard": {"linear_sensitivity": 0.15, "quadratic_sensitivity": 0.60, "heat_spike": 0.30},
}


def temperature_for_circuit(circuit_key, temperature_index):
    """Nhiệt độ mặt đường: mát hơn chuẩn, đúng chuẩn, hoặc nóng hơn chuẩn."""
    offsets = (-8.0, 0.0, 10.0)
    return REFERENCE_TRACK_TEMPERATURE[circuit_key] + offsets[temperature_index]


def wear_at_temperature(compound_name, linear_wear, quadratic_wear, temperature_ratio):
    """Chỉnh độ mòn khi mặt đường lệch khỏi nhiệt độ chuẩn."""
    sensitivity = THERMAL_WEAR[compound_name]
    heat_spike = max(0.0, temperature_ratio) ** 2
    adjusted_linear = linear_wear * (1.0 + sensitivity["linear_sensitivity"] * temperature_ratio)
    adjusted_quadratic = quadratic_wear * (
        1.0
        + sensitivity["quadratic_sensitivity"] * temperature_ratio
        + sensitivity["heat_spike"] * heat_spike
    )
    # Không cho độ mòn tụt quá thấp khi trời lạnh.
    adjusted_linear = max(linear_wear * 0.20, adjusted_linear)
    adjusted_quadratic = max(quadratic_wear * 0.10, adjusted_quadratic)
    return adjusted_linear, adjusted_quadratic


def tyre_limit_at_temperature(nominal_limit, temperature_ratio):
    """Hạ số vòng an toàn khi mặt đường nóng hơn chuẩn từ 20% trở lên."""
    if temperature_ratio <= 0.20:
        return nominal_limit
    heat_ratio = min(1.5, temperature_ratio)
    reduction = int(round(nominal_limit * 0.20 * heat_ratio))
    return max(8, nominal_limit - reduction)


def load_circuit_numbers(circuit_key, coefficient_source):
    """Đọc số liệu chặng từ bảng cấu hình, hoặc đè hệ số lốp bằng file đã fit."""
    configuration = RACE_CONFIGS[circuit_key]
    compounds = {}
    for compound_key, row in configuration["compounds"].items():
        compound_name = compound_key.capitalize()
        compounds[compound_name] = {
            "base_time": row["t_base"],
            "linear_wear": row["d1"],
            "quadratic_wear": row["d2"],
            "tyre_limit": row["l_max"],
            "color": row["color"],
        }

    numbers = {
        "circuit_key": circuit_key,
        "circuit_name": configuration["name"],
        "total_laps": configuration["n_laps"],
        "pit_loss_seconds": configuration["pit_loss"],
        "fuel_effect_per_lap": configuration["alpha_fuel"],
        "track_effect_per_lap": configuration["gamma_track"],
        "fuel_load_kg": configuration["fuel_load_kg"],
        "fuel_burn_kg_per_lap": configuration["fuel_burn_kg_per_lap"],
        "compounds": compounds,
    }
    if coefficient_source == "nominal":
        return numbers

    fitted_path = ROOT_DIR / "models" / f"tyre_params_{circuit_key}.json"
    with open(fitted_path, encoding="utf-8") as fitted_file:
        fitted = json.load(fitted_file)
    numbers["total_laps"] = fitted["total_laps"]
    numbers["pit_loss_seconds"] = fitted["t_pit"]
    numbers["fuel_effect_per_lap"] = fitted["alpha_fuel"]
    numbers["track_effect_per_lap"] = fitted["gamma_track"]
    for compound_name, row in fitted["compounds"].items():
        if compound_name not in compounds:
            continue
        compounds[compound_name]["base_time"] = row["t_base"]
        compounds[compound_name]["linear_wear"] = row["d1"]
        compounds[compound_name]["quadratic_wear"] = row["d2"]
        compounds[compound_name]["tyre_limit"] = row["l_max"]
    return numbers


def apply_track_temperature(numbers, track_temperature):
    """Trả về bản số liệu đã chỉnh độ mòn và giới hạn lốp theo nhiệt độ."""
    reference_temperature = REFERENCE_TRACK_TEMPERATURE[numbers["circuit_key"]]
    temperature_ratio = (track_temperature - reference_temperature) / reference_temperature
    adjusted_compounds = {}
    for compound_name, row in numbers["compounds"].items():
        linear_wear, quadratic_wear = wear_at_temperature(
            compound_name,
            row["linear_wear"],
            row["quadratic_wear"],
            temperature_ratio,
        )
        adjusted_compounds[compound_name] = {
            "base_time": row["base_time"],
            "linear_wear": linear_wear,
            "quadratic_wear": quadratic_wear,
            "tyre_limit": tyre_limit_at_temperature(row["tyre_limit"], temperature_ratio),
            "color": row["color"],
        }
    adjusted = dict(numbers)
    adjusted["compounds"] = adjusted_compounds
    adjusted["track_temperature"] = track_temperature
    adjusted["reference_temperature"] = reference_temperature
    return adjusted


def make_lap_time_function(numbers):
    """Tạo hàm tính thời gian một vòng từ hệ số của chặng."""
    compounds = numbers["compounds"]
    fuel_effect_per_lap = numbers["fuel_effect_per_lap"]
    track_effect_per_lap = numbers["track_effect_per_lap"]

    def lap_time_seconds(compound_name, tyre_age, race_lap, total_laps):
        """Cộng thời gian gốc, mòn lốp, xe nhẹ xăng và mặt đường bám hơn."""
        row = compounds[compound_name]
        tyre_wear = row["linear_wear"] * tyre_age + row["quadratic_wear"] * (tyre_age ** 2)
        fuel_delta = fuel_effect_per_lap * (total_laps - race_lap)
        track_delta = track_effect_per_lap * race_lap
        return row["base_time"] + tyre_wear + fuel_delta - track_delta

    return lap_time_seconds


def total_time_of_strategy(strategy, lap_time_function, pit_loss_seconds):
    """Tổng thời gian gốc của chiến lược, chưa tính cờ và khí bẩn."""
    total_laps = sum(length for _, length in strategy)
    total_time = 0.0
    race_lap = 1
    for stint_index, (compound_name, stint_length) in enumerate(strategy):
        for tyre_age in range(1, stint_length + 1):
            total_time += lap_time_function(compound_name, tyre_age, race_lap, total_laps)
            race_lap += 1
        is_last_stint = stint_index == len(strategy) - 1
        if not is_last_stint:
            total_time += pit_loss_seconds
    return total_time


def build_race_segments(strategy, lap_time_function, pit_loss_seconds):
    """Tạo danh sách từng vòng và từng lần pit."""
    total_laps = sum(length for _, length in strategy)
    segments = []
    total_time = 0.0
    race_lap = 1
    for stint_index, (compound_name, stint_length) in enumerate(strategy, start=1):
        for tyre_age in range(1, stint_length + 1):
            duration = lap_time_function(compound_name, tyre_age, race_lap, total_laps)
            segments.append({
                "kind": "lap",
                "compound": compound_name,
                "tyre_age": tyre_age,
                "race_lap": race_lap,
                "base_seconds": duration,
                "stint_index": stint_index,
            })
            total_time += duration
            race_lap += 1
        is_last_stint = stint_index == len(strategy)
        if not is_last_stint:
            segments.append({
                "kind": "pit",
                "compound": compound_name,
                "tyre_age": stint_length,
                "race_lap": race_lap - 1,
                "base_seconds": pit_loss_seconds,
                "stint_index": stint_index,
            })
            total_time += pit_loss_seconds
    return segments, total_time


def monza_strategies(configuration):
    """Ba chiến lược Monza. Holland dùng Medium 24 rồi Hard 29 vì tổng đó là 4508.197 giây."""
    verstappen_strategy = [
        (compound_name.capitalize(), stint_length)
        for compound_name, stint_length in configuration["verstappen_2023"]["strategy"]
    ]
    return [
        {
            "name": "GA Optimal (2-Stop)",
            "color": (235, 45, 45),
            "strategy": [("Medium", 20), ("Soft", 14), ("Medium", 19)],
            "is_reference": False,
        },
        {
            "name": "Verstappen (1-Stop)",
            "color": (45, 135, 245),
            "strategy": verstappen_strategy,
            "is_reference": True,
        },
        {
            "name": "Holland GA (1-Stop)",
            "color": (245, 195, 35),
            "strategy": [("Medium", 24), ("Hard", 29)],
            "is_reference": False,
        },
    ]


def shortest_one_stop(first_compound, second_compound, numbers, lap_time_function):
    """Chia một lần pit sao cho tổng thời gian nhỏ nhất và không vượt giới hạn lốp."""
    total_laps = numbers["total_laps"]
    pit_loss_seconds = numbers["pit_loss_seconds"]
    first_limit = numbers["compounds"][first_compound]["tyre_limit"]
    second_limit = numbers["compounds"][second_compound]["tyre_limit"]
    best_strategy = None
    best_time = None
    longest_first_stint = min(first_limit, total_laps - 4)
    for first_length in range(4, longest_first_stint + 1):
        second_length = total_laps - first_length
        if second_length < 4 or second_length > second_limit:
            continue
        strategy = [(first_compound, first_length), (second_compound, second_length)]
        total_time = total_time_of_strategy(strategy, lap_time_function, pit_loss_seconds)
        if best_time is None or total_time < best_time:
            best_strategy = strategy
            best_time = total_time
    return best_strategy


def shortest_two_stop(numbers, lap_time_function):
    """Tìm chiến lược hai lần pit ngắn nhất trong giới hạn tuổi lốp."""
    total_laps = numbers["total_laps"]
    pit_loss_seconds = numbers["pit_loss_seconds"]
    compound_names = ["Soft", "Medium", "Hard"]
    best_strategy = None
    best_time = None
    for first_compound in compound_names:
        for second_compound in compound_names:
            for third_compound in compound_names:
                used = {first_compound, second_compound, third_compound}
                if len(used) < 2:
                    continue
                first_limit = numbers["compounds"][first_compound]["tyre_limit"]
                second_limit = numbers["compounds"][second_compound]["tyre_limit"]
                third_limit = numbers["compounds"][third_compound]["tyre_limit"]
                for first_length in range(4, first_limit + 1):
                    for second_length in range(4, second_limit + 1):
                        third_length = total_laps - first_length - second_length
                        if third_length < 4 or third_length > third_limit:
                            continue
                        strategy = [
                            (first_compound, first_length),
                            (second_compound, second_length),
                            (third_compound, third_length),
                        ]
                        total_time = total_time_of_strategy(strategy, lap_time_function, pit_loss_seconds)
                        if best_time is None or total_time < best_time:
                            best_strategy = strategy
                            best_time = total_time
    return best_strategy


def silverstone_strategies(numbers, lap_time_function):
    """Ba chiến lược Silverstone: hai lần pit ngắn nhất, rồi hai kiểu một lần pit."""
    two_stop = shortest_two_stop(numbers, lap_time_function)
    medium_hard = shortest_one_stop("Medium", "Hard", numbers, lap_time_function)
    soft_hard = shortest_one_stop("Soft", "Hard", numbers, lap_time_function)
    if two_stop is None or medium_hard is None or soft_hard is None:
        half_distance = numbers["total_laps"] // 2
        medium_hard = [("Medium", half_distance), ("Hard", numbers["total_laps"] - half_distance)]
        if two_stop is None:
            two_stop = [("Medium", 16), ("Hard", 18), ("Medium", numbers["total_laps"] - 34)]
        if soft_hard is None:
            soft_hard = [("Soft", 12), ("Hard", numbers["total_laps"] - 12)]
    return [
        {
            "name": "Best 2-stop",
            "color": (235, 45, 45),
            "strategy": two_stop,
            "is_reference": False,
        },
        {
            "name": "Medium-Hard (1-Stop)",
            "color": (45, 135, 245),
            "strategy": medium_hard,
            "is_reference": True,
        },
        {
            "name": "Soft-Hard (1-Stop)",
            "color": (245, 195, 35),
            "strategy": soft_hard,
            "is_reference": False,
        },
    ]


def strategy_text(strategy):
    """Viết chiến lược thành một dòng, ví dụ Medium 20, Soft 14."""
    return ", ".join(f"{compound_name} {stint_length}" for compound_name, stint_length in strategy)


class RaceCar:
    """Một xe với chiến lược pit, thời gian gốc và trạng thái đang chạy."""

    def __init__(
        self,
        name,
        color,
        strategy,
        numbers,
        lap_time_function,
        time_scale,
        starting_order,
        is_reference,
    ):
        """Dựng timeline gốc và đặt xe ở đầu vòng 1."""
        self.name = name
        self.color = color
        self.strategy = strategy
        self.strategy_line = strategy_text(strategy)
        self.total_laps = sum(stint_length for _, stint_length in strategy)
        self.time_scale = time_scale
        self.starting_order = starting_order
        self.is_reference = is_reference
        self.fuel_load_kg = numbers["fuel_load_kg"]
        self.fuel_burn_kg_per_lap = numbers["fuel_burn_kg_per_lap"]
        self.tyre_limits = {
            compound_name: row["tyre_limit"]
            for compound_name, row in numbers["compounds"].items()
        }
        self.compound_colors = {
            compound_name: row["color"]
            for compound_name, row in numbers["compounds"].items()
        }
        self.segments, self.base_race_time = build_race_segments(
            strategy,
            lap_time_function,
            numbers["pit_loss_seconds"],
        )
        self.fallback_lap_seconds = self.segments[0]["base_seconds"]
        self.current_segment_index = 0
        self.seconds_into_segment = 0.0
        self.locked_duration = None
        self.elapsed = 0.0
        self.finished = False
        self.progress = 0.0
        self.laps_completed = 0
        self.place = starting_order + 1
        self.gap_to_leader_seconds = 0.0
        self.delta_to_reference_seconds = 0.0
        self.traffic_note = "clean air"
        self.status = "racing"
        self.current_compound = strategy[0][0]
        self.current_tyre_age = 1
        self.current_tyre_limit = self.tyre_limits[self.current_compound]
        self.compound_color = self.compound_colors[self.current_compound]
        self.lock_current_segment(1.0, 1.0, 0.0, "clean air")

    def current_segment(self):
        """Đoạn xe đang chạy. Hết chặng thì không còn đoạn."""
        if self.finished or self.current_segment_index >= len(self.segments):
            return None
        return self.segments[self.current_segment_index]

    def refresh_status(self):
        """Cập nhật vị trí trên đường, tuổi lốp và chữ trạng thái."""
        if self.finished:
            self.status = "finished"
            self.progress = 1.0
            self.laps_completed = self.total_laps
            return
        segment = self.current_segment()
        self.current_compound = segment["compound"]
        self.current_tyre_age = segment["tyre_age"]
        self.current_tyre_limit = self.tyre_limits[segment["compound"]]
        self.compound_color = self.compound_colors[segment["compound"]]
        if segment["kind"] == "pit":
            self.status = "pit lane"
            self.progress = 0.05
            self.laps_completed = segment["race_lap"]
            return
        self.laps_completed = segment["race_lap"] - 1
        if self.locked_duration:
            self.progress = min(0.999, self.seconds_into_segment / self.locked_duration)
        else:
            self.progress = 0.0
        if self.current_tyre_age > self.current_tyre_limit:
            self.status = "past tyre limit"
        else:
            self.status = "racing"

    def lock_current_segment(self, lap_time_multiplier, pit_time_multiplier, traffic_extra, traffic_note):
        """Giữ thời lượng đoạn hiện tại đến khi xe chạy hết đoạn đó."""
        segment = self.current_segment()
        if segment is None:
            return
        if segment["kind"] == "lap":
            paced_seconds = (segment["base_seconds"] + traffic_extra) * lap_time_multiplier
            self.traffic_note = traffic_note
        else:
            paced_seconds = segment["base_seconds"] * pit_time_multiplier
            self.traffic_note = "pit lane"
        self.locked_duration = max(0.1, paced_seconds)
        self.refresh_status()

    def advance(self, real_seconds):
        """Chạy tiếp trong đoạn hiện tại. Trả về phần thời gian thực chưa dùng."""
        if self.finished:
            return 0.0
        if self.locked_duration is None:
            return real_seconds
        race_step = real_seconds * self.time_scale
        room = self.locked_duration - self.seconds_into_segment
        if race_step + 1e-9 < room:
            self.seconds_into_segment += race_step
            self.elapsed += race_step
            self.refresh_status()
            return 0.0
        self.elapsed += max(0.0, room)
        self.seconds_into_segment = 0.0
        self.current_segment_index += 1
        self.locked_duration = None
        if self.current_segment_index >= len(self.segments):
            self.finished = True
            self.refresh_status()
            return 0.0
        self.refresh_status()
        unused_race_seconds = race_step - room
        if self.time_scale <= 0:
            return 0.0
        return max(0.0, unused_race_seconds / self.time_scale)

    def race_distance(self):
        """Số vòng đã đi trên đường, gồm cả phần vòng đang chạy."""
        if self.finished:
            return float(self.total_laps)
        segment = self.current_segment()
        if segment["kind"] == "pit":
            return float(segment["race_lap"])
        return (segment["race_lap"] - 1) + self.progress

    def seconds_per_lap_now(self):
        """Thời gian gốc của vòng hiện tại, dùng để đổi khoảng cách ra giây."""
        segment = self.current_segment()
        if segment is not None and segment["kind"] == "lap":
            return segment["base_seconds"]
        return self.fallback_lap_seconds

    def fuel_remaining_kg(self):
        """Xăng còn lại sau các vòng đã chạy xong."""
        burned = self.laps_completed * self.fuel_burn_kg_per_lap
        return max(0.0, self.fuel_load_kg - burned)

    def laps_until_pit(self):
        """Số vòng còn lại trước lần pit kế tiếp. Hết pit thì trả về None."""
        if self.finished:
            return None
        laps_left = 0
        for index in range(self.current_segment_index, len(self.segments)):
            segment = self.segments[index]
            if segment["kind"] == "pit":
                return laps_left
            laps_left += 1
        return None

    def projected_race_time(self):
        """Thời gian về đích ước tính từ quãng đã chạy và pace gốc của phần còn lại."""
        if self.finished:
            return self.elapsed
        remaining = 0.0
        for index, segment in enumerate(self.segments):
            if index < self.current_segment_index:
                continue
            if index == self.current_segment_index and self.locked_duration is not None:
                remaining += max(0.0, self.locked_duration - self.seconds_into_segment)
            else:
                remaining += segment["base_seconds"]
        return self.elapsed + remaining


def cars_in_order(cars):
    """Xếp xe theo quãng đường. Hòa thì xe xuất phát trước đứng trên."""
    return sorted(
        cars,
        key=lambda car: (car.race_distance(), -car.starting_order),
        reverse=True,
    )


def gap_to_car_ahead(car, cars):
    """Số giây cách xe gần nhất đang chạy phía trước. Không có thì None."""
    closest_gap = None
    for other in cars:
        if other is car or other.finished:
            continue
        other_segment = other.current_segment()
        if other_segment is None or other_segment["kind"] != "lap":
            continue
        laps_ahead = other.race_distance() - car.race_distance()
        if laps_ahead <= 0.000001:
            continue
        gap_seconds = laps_ahead * car.seconds_per_lap_now()
        if closest_gap is None or gap_seconds < closest_gap:
            closest_gap = gap_seconds
    return closest_gap


def traffic_extra_seconds(car, cars, dirty_air_parameters):
    """Cộng giây khí bẩn hoặc trừ giây DRS theo khoảng cách tới xe trước."""
    segment = car.current_segment()
    if segment is None or segment["kind"] != "lap":
        return 0.0, "pit lane"
    gap_seconds = gap_to_car_ahead(car, cars)
    extra_seconds = 0.0
    note = "clean air"
    if gap_seconds is not None and gap_seconds <= dirty_air_parameters["gap_threshold"]:
        extra_seconds += dirty_air_parameters["time_penalty_per_lap"]
        note = "dirty air"
    if gap_seconds is not None and gap_seconds <= dirty_air_parameters["drs_gap_threshold"]:
        extra_seconds -= dirty_air_parameters["drs_benefit"]
        note = "DRS"
    return extra_seconds, note


def assign_race_order(cars):
    """Ghi hạng, khoảng cách tới xe dẫn đầu và lệch thời gian so với xe mốc."""
    ordered = cars_in_order(cars)
    leader = ordered[0]
    reference_car = next(car for car in cars if car.is_reference)
    for place, car in enumerate(ordered, start=1):
        car.place = place
        if car is leader:
            car.gap_to_leader_seconds = 0.0
        else:
            laps_behind = leader.race_distance() - car.race_distance()
            car.gap_to_leader_seconds = laps_behind * car.seconds_per_lap_now()
        car.delta_to_reference_seconds = car.projected_race_time() - reference_car.projected_race_time()


class RaceControl:
    """Cờ xanh, safety car và virtual safety car cho cả đoàn xe."""

    def __init__(self, total_laps, safety_parameters, random_source=None):
        """Bốc trước tối đa một safety car theo xác suất trong bảng."""
        self.total_laps = total_laps
        self.safety_parameters = safety_parameters
        self.random_source = random_source or random.Random()
        self.mode = "green"
        self.laps_remaining = 0
        self.planned_start_lap = None
        self.planned_length = 0
        self.counted_lap = 0
        self.show_laps = 0
        self.message = ""
        self.draw_planned_safety_car()

    def draw_planned_safety_car(self):
        """Bốc có safety car hay không, vòng bắt đầu và số vòng kéo dài."""
        chance = 1.0 - math.exp(-self.safety_parameters["poisson_lambda"])
        if self.random_source.random() > chance:
            self.planned_start_lap = None
            self.planned_length = 0
            return
        first_lap = self.safety_parameters["sc_lap_min"]
        last_lap = int(self.total_laps * self.safety_parameters["sc_lap_max_fraction"])
        if last_lap < first_lap:
            self.planned_start_lap = None
            self.planned_length = 0
            return
        shortest, longest = self.safety_parameters["sc_duration_laps"]
        self.planned_start_lap = self.random_source.randint(first_lap, last_lap)
        self.planned_length = self.random_source.randint(shortest, longest)

    def lap_time_multiplier(self):
        """Xe chạy chậm hơn khi có cờ, nên một vòng tốn nhiều giây hơn."""
        if self.mode == "safety_car":
            return 1.0 / self.safety_parameters["sc_speed_factor"]
        if self.mode == "virtual_safety_car":
            return 1.0 / self.safety_parameters["vsc_speed_factor"]
        return 1.0

    def pit_time_multiplier(self):
        """Pit ngắn hơn khi cả đoàn đang chạy chậm sau cờ."""
        if self.mode == "safety_car":
            return self.safety_parameters["sc_pit_loss_reduction"]
        if self.mode == "virtual_safety_car":
            return self.safety_parameters["vsc_pit_loss_reduction"]
        return 1.0

    def flag_text(self):
        """Dòng trạng thái cờ cho bảng bên phải."""
        lap_word = "lap" if self.show_laps == 1 else "laps"
        if self.mode == "safety_car":
            return f"Flag: safety car, {self.show_laps} {lap_word} left"
        if self.mode == "virtual_safety_car":
            return f"Flag: virtual safety car, {self.show_laps} {lap_word} left"
        return "Flag: green"

    def planned_text(self):
        """Dòng kế hoạch safety car đã bốc lúc đầu chặng."""
        if self.planned_start_lap is None:
            return "Planned safety car: none"
        return f"Planned safety car: lap {self.planned_start_lap}, {self.planned_length} laps"

    def within_window(self, race_lap):
        """Safety car chỉ nằm từ vòng 5 đến trước 85% số vòng."""
        first_lap = self.safety_parameters["sc_lap_min"]
        last_lap = int(self.total_laps * self.safety_parameters["sc_lap_max_fraction"])
        return first_lap <= race_lap <= last_lap

    def request_flag(self, mode, race_lap):
        """Bật cờ bằng phím nếu đang cờ xanh và còn trong khoảng vòng cho phép."""
        if self.mode != "green":
            self.message = "A flag is already out"
            return False
        if not self.within_window(race_lap):
            self.message = "Flag only from lap 5 to 85 percent"
            return False
        shortest, longest = self.safety_parameters["sc_duration_laps"]
        self.mode = mode
        self.laps_remaining = self.random_source.randint(shortest, longest)
        self.show_laps = self.laps_remaining
        self.counted_lap = race_lap
        self.planned_start_lap = None
        self.message = ""
        return True

    def note_progress(self, cars):
        """Bật safety car đã bốc khi xe dẫn đầu bước vào đúng vòng đó."""
        leader = cars_in_order(cars)[0]
        if leader.finished:
            return
        segment = leader.current_segment()
        if segment is None or segment["kind"] != "lap":
            return
        race_lap = segment["race_lap"]
        if (
            self.mode == "green"
            and self.planned_start_lap is not None
            and race_lap >= self.planned_start_lap
        ):
            self.mode = "safety_car"
            self.laps_remaining = max(0, self.planned_length - 1)
            self.show_laps = self.planned_length
            self.counted_lap = race_lap
            self.planned_start_lap = None
            self.message = ""

    def pace_for_new_lap(self, car, cars):
        """Hệ số thời gian vòng. Chỉ xe dẫn đầu làm giảm số vòng cờ còn lại."""
        segment = car.current_segment()
        if segment is None or segment["kind"] != "lap":
            return self.lap_time_multiplier()
        race_lap = segment["race_lap"]
        leader = cars_in_order(cars)[0]
        if car is leader and self.mode != "green" and race_lap != self.counted_lap:
            self.counted_lap = race_lap
            if self.laps_remaining <= 0:
                self.mode = "green"
                self.laps_remaining = 0
                self.show_laps = 0
            else:
                self.laps_remaining -= 1
                self.show_laps = self.laps_remaining + 1
        return self.lap_time_multiplier()


def leader_race_lap(cars):
    """Vòng đua hiện tại của xe đang dẫn đầu."""
    leader = cars_in_order(cars)[0]
    if leader.finished:
        return leader.total_laps
    return leader.laps_completed + 1


def advance_cars(cars, race_control, real_seconds):
    """Tiến cả đoàn xe. Sang vòng mới thì gắn lại cờ, khí bẩn và DRS."""
    pending = [real_seconds for _ in cars]
    for _guard in range(8):
        still_running = False
        for wait, car in zip(pending, cars):
            if wait > 1e-8 and not car.finished:
                still_running = True
                break
        if not still_running:
            break
        race_control.note_progress(cars)
        for car in cars_in_order(cars):
            if car.finished or car.locked_duration is not None:
                continue
            segment = car.current_segment()
            if segment is not None and segment["kind"] == "lap":
                lap_multiplier = race_control.pace_for_new_lap(car, cars)
                extra_seconds, traffic_note = traffic_extra_seconds(car, cars, DIRTY_AIR_PARAMS)
                pit_multiplier = 1.0
            else:
                lap_multiplier = 1.0
                pit_multiplier = race_control.pit_time_multiplier()
                extra_seconds = 0.0
                traffic_note = "pit lane"
            car.lock_current_segment(
                lap_multiplier,
                pit_multiplier,
                extra_seconds,
                traffic_note,
            )
        for index, car in enumerate(cars):
            if pending[index] <= 1e-8 or car.finished:
                continue
            pending[index] = car.advance(pending[index])


def demo_field(circuit_key, track_temperature, coefficient_source, time_scale, random_source=None):
    """Dựng ba xe và bộ cờ cho một lần chạy."""
    configuration = RACE_CONFIGS[circuit_key]
    numbers = apply_track_temperature(
        load_circuit_numbers(circuit_key, coefficient_source),
        track_temperature,
    )
    lap_time_function = make_lap_time_function(numbers)
    if circuit_key == "monza":
        specifications = monza_strategies(configuration)
    else:
        specifications = silverstone_strategies(numbers, lap_time_function)

    cars = []
    for starting_order, specification in enumerate(specifications):
        cars.append(RaceCar(
            name=specification["name"],
            color=specification["color"],
            strategy=specification["strategy"],
            numbers=numbers,
            lap_time_function=lap_time_function,
            time_scale=time_scale,
            starting_order=starting_order,
            is_reference=specification["is_reference"],
        ))
    race_control = RaceControl(numbers["total_laps"], SC_PARAMS, random_source)
    assign_race_order(cars)
    return cars, race_control, numbers
