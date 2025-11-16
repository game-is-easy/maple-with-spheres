from scripts.gameUI import *
import os
import yaml
from typing import Tuple, List, Dict, Union


class Map:
    def __init__(self, map_name: str):
        self.map_name = map_name
        self.minimap_region: Union[Box, None] = None
        self.start_position: Union[Position, None] = None  # also class-specified placement position
        self.standby_position: Union[Position, None] = None
        self.erda_position: Union[Position, None] = None
        self.sphere_positions: List[Position] = []
        self.loot_series: List[Tuple[Position | str, Dict[str, int]]] = []
        self.tp_positions: List[TpPosition] = []
        self.reset_position: Union[Position, None] = None
        self.platforms: Dict[int, List[Dict[str, Union[List[int], int]]]] = {}
        self.platforms_ordered_by_x: Dict[int, List[int]] = {}
        self.initiate_map()
        self.tp_equiv_distance = 0
        self.tp_positions_coverage = [100, 50]  # x-range, y-range

    def set_tp_equiv_distance(self, tp_equiv_distance):
        self.tp_equiv_distance = tp_equiv_distance

    def set_tp_positions_coverage(self, coverage: List[int]):
        self.tp_positions_coverage = coverage

    def set_tp_positions(self, positions: List[Position], loop=False):
        assert len(positions) > 1
        tp_positions = [TpPosition(position=position) for position in positions]
        for i in range(len(tp_positions)):
            tp_position = tp_positions[i].find_in_series(self.tp_positions)
            if tp_position is None:
                tp_position = tp_positions[i]
                self.tp_positions.append(tp_position)
            if i < len(positions) - 1:
                tp_position.set_next(tp_positions[i+1].find_in_series(self.tp_positions) or tp_positions[i+1])
            elif loop:
                tp_position.set_next(tp_positions[0].find_in_series(self.tp_positions) or tp_positions[0])


    def set_sphere_positions(self, sphere_positions: List[Position]):
        self.sphere_positions = sphere_positions

    def set_loot_series(self, loop_series: List[Position]):
        self.loot_series = loop_series

    def set_erda_position(self, erda_position: Position):
        self.erda_position = erda_position

    def set_reset_position(self, reset_position: Position):
        self.reset_position = reset_position

    def set_start_position(self, start_position: Position):
        self.start_position = start_position

    def set_standby_position(self, standby_position: Position = None):
        self.standby_position = standby_position or self.start_position

    def initiate_map(self, tp_equiv_distance=50):
        self.set_tp_equiv_distance(tp_equiv_distance)
        maps = read_map_yaml()
        map_obj = None
        for m in maps:
            if m["name"].lower() == self.map_name.lower():
                map_obj = m
                break
        if map_obj is None:
            return
        if map_obj.get("start_position"):
            self.set_start_position(Position(*map_obj["start_position"]))
        if map_obj.get("standby_position"):
            self.set_standby_position(Position(*map_obj["standby_position"]))
        else:
            self.set_standby_position()
        if map_obj.get("erda_position"):
            self.set_erda_position(Position(*map_obj["erda_position"]))
        if map_obj.get("reset_position"):
            self.set_reset_position(Position(*map_obj["reset_position"]))
        if map_obj.get("sphere_positions"):
            self.set_sphere_positions([Position(*p) for p in map_obj["sphere_positions"]])
        if map_obj.get("loot_series"):
            # print(map_obj["loot_series"])
            for loot_event in map_obj["loot_series"]:
                if loot_event.get("position"):
                    self.loot_series.append((Position(*loot_event["position"]), loot_event.get("params")))
                if loot_event.get("action"):
                    self.loot_series.append((loot_event["action"], loot_event.get("params")))
        if map_obj.get("tp_position_series"):
            for series in map_obj["tp_position_series"]:
                self.set_tp_positions([Position(*p) for p in series["positions"]], series["loop"])
        if map_obj.get("tp_positions_coverage"):
            self.set_tp_positions_coverage(map_obj["tp_positions_coverage"])
        if map_obj.get("platforms"):
            for platform in map_obj["platforms"]:
                if platform['y'] in self.platforms:
                    self.platforms[platform['y']].append({"edges": platform['x'], "rope": platform.get('rope')})
                else:
                    self.platforms.update({platform['y']: [{"edges": platform['x'], "rope": platform.get('rope')}]})
        self.minimap_region = extract_minimap_region(map_obj["region"].lower())

    def get_platform(self, position: Position):
        for platform in self.platforms.get(position.y) or []:
            if platform["edges"][0] <= position.x <= platform["edges"][1]:
                return platform

    def get_edges_at(self, position: Position):
        platform = self.get_platform(position)
        if platform is not None:
            return platform["edges"]

    def get_all_levels_at(self, x: int):
        levels = []
        for y, platforms in self.platforms.items():
            for platform in platforms:
                if platform['edges'][0] <= x <= platform['edges'][1]:
                    levels.append(y)
        return levels

    def total_distance_between(self, position_1: Union[Position, 'TpPosition'], position_2: Union[Position, 'TpPosition']):
        return abs(position_1.x - position_2.x) + abs(position_1.y - position_2.y)

    def get_tp_route_to_target(self, current_position: Position, target_position: Position, max_tp_count=2, extra_punishment=0):
        shortest_equiv_distance_to_target = self.total_distance_between(current_position, target_position)
        # print(f"non-tp distance: {shortest_equiv_distance_to_target}")
        inter_position = target_position
        tp_count = 0
        tolerance_x, tolerance_y = self.tp_positions_coverage
        for tp_position in self.tp_positions:
            if not is_overlap(current_position, tp_position, tolerance_x=tolerance_x, tolerance_y=tolerance_y):
                continue
            distance_to_tp = self.total_distance_between(current_position, tp_position)
            # print(tp_position.as_position())
            for count in range(1, max_tp_count + 1):
                distance_from_tp_to_target = self.total_distance_between(tp_position.next(count), target_position)
                equiv_distance_to_target = distance_to_tp + distance_from_tp_to_target + self.tp_equiv_distance * count + extra_punishment
                # print(f"distance: {distance_from_tp_to_target}, punishment: {extra_punishment}, tp_count: {count}, equiv_distance: {equiv_distance_to_target}")
                if equiv_distance_to_target < shortest_equiv_distance_to_target:
                    inter_position = tp_position.as_position()
                    tp_count = count
        # print(inter_position, tp_count)
        return inter_position, tp_count

    def estimate_time_separation(self, from_position, to_position):
        return

    def target_level_horizontal_move(self, from_position, to_position):
        return


class TpPosition:
    def __init__(self, position=None, position_x=None, position_y=None, next_position=None):
        self.x: int = position_x if position_x else position.x
        self.y: int = position_y if position_y else position.y
        self.position: Position = position if position else Position(position_x, position_y)
        self._next: TpPosition = next_position

    def __str__(self):
        return f"x={self.x} y={self.y} next=({self._next.x}, {self._next.y})"

    def next(self, count=1):
        if count > 1:
            return self._next.next(count=count-1)
        return self._next

    def set_next(self, next_position: 'TpPosition'):
        self._next = next_position

    def as_position(self):
        return Position(self.x, self.y)

    def is_same_as(self, tp_position: 'TpPosition'):
        return self.x == tp_position.x and self.y == tp_position.y

    def find_in_series(self, tp_series: List['TpPosition']):
        for tp_position in tp_series:
            if self.is_same_as(tp_position):
                return tp_position
        return None


def read_map_yaml():
    dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
    file_path = os.path.join(dir, "resources", "maps.yaml")
    with open(file_path) as f:
        result = yaml.safe_load(f)
    return result


if __name__ == '__main__':
    map = Map("Top Deck Passage 6")
    # print(map.loot_series)
    print(map.tp_positions[0] == map.tp_positions[0].next().next().next())
