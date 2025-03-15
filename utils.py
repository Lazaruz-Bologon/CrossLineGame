import heapq
import numpy as np
import time
from typing import List, Tuple, Dict, Set, Optional
from collections import defaultdict

DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]
DIRECTION_NAMES = ["上", "右", "下", "左"]

def create_board(size: int) -> np.ndarray:
    return np.zeros((size, size), dtype=int)

def add_pairs_to_board(board: np.ndarray, pairs: Dict[int, List[Tuple[int, int]]]) -> np.ndarray:
    board_copy = board.copy()
    for color, positions in pairs.items():
        for pos in positions:
            board_copy[pos[0], pos[1]] = color
    return board_copy

def visualize_board(board: np.ndarray, paths: Optional[Dict[int, List[Tuple[int, int]]]] = None) -> None:
    size = board.shape[0]
    visualization = [['·' for _ in range(size)] for _ in range(size)]
    for i in range(size):
        for j in range(size):
            if board[i, j] > 0:
                visualization[i][j] = str(board[i, j])
    if paths:
        path_symbols = {1: '1', 2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'A'}
        for color, path in paths.items():
            symbol = path_symbols.get(color, str(color))
            for x, y in path:
                if board[x, y] == 0:
                    visualization[x][y] = symbol
    for row in visualization:
        print(' '.join(row))
    print()

def is_valid_position(pos: Tuple[int, int], size: int) -> bool:
    return 0 <= pos[0] < size and 0 <= pos[1] < size

def get_edge(pos1, pos2):
    if pos1 > pos2:
        pos1, pos2 = pos2, pos1
    return (pos1, pos2)

def check_edge_crossing(path1, path2):
    edges1 = set()
    for i in range(len(path1) - 1):
        edges1.add(get_edge(path1[i], path1[i+1]))
    for i in range(len(path2) - 1):
        edge = get_edge(path2[i], path2[i+1])
        if edge in edges1:
            return True
    return False

def is_edge_free(pos1, pos2, used_edges):
    return get_edge(pos1, pos2) not in used_edges

def get_path_cost(path: List[Tuple[int, int]], with_turning_cost: bool = False) -> int:
    if len(path) <= 2:
        return len(path) - 1
    cost = len(path) - 1
    if with_turning_cost:
        turns = 0
        prev_dir = None
        for i in range(1, len(path)):
            curr_dir = (path[i][0] - path[i-1][0], path[i][1] - path[i-1][1])
            if prev_dir is not None and prev_dir != curr_dir:
                turns += 1
            prev_dir = curr_dir
        cost += turns * 2
    return cost

def encode_state(x: int, y: int, dir_idx: int) -> str:
    return f"{x},{y},{dir_idx}"

def decode_state(code: str) -> Tuple[int, int, int]:
    parts = code.split(',')
    if len(parts) == 3:
        x, y, dir_idx = int(parts[0]), int(parts[1]), int(parts[2])
        return (x, y, dir_idx)
    return (-1, -1, -1)

def bidirectional_astar_search(board: np.ndarray, start: Tuple[int, int], end: Tuple[int, int], occupied_cells: Set[Tuple[int, int]], with_turning_cost: bool = False, color: int = 0, verbose: bool = True, used_edges: Set[Tuple[Tuple[int, int], Tuple[int, int]]] = None) -> List[Tuple[int, int]]:
    if used_edges is None:
        used_edges = set()
    start_time = time.time()
    size = board.shape[0]
    if not is_valid_position(start, size) or not is_valid_position(end, size):
        if verbose:
            print(f"颜色 {color} 的起点或终点无效: {start} -> {end}")
        return []
    if abs(start[0] - end[0]) + abs(start[1] - end[1]) == 1:
        return [start, end]
    if start == end:
        return [start]
    distance = abs(start[0] - end[0]) + abs(start[1] - end[1])
    if size <= 8:
        min_x, max_x = 0, size - 1
        min_y, max_y = 0, size - 1
    else:
        margin = min(max(5, distance), size // 2)
        min_x = max(0, min(start[0], end[0]) - margin)
        max_x = min(size - 1, max(start[0], end[0]) + margin)
        min_y = max(0, min(start[1], end[1]) - margin)
        max_y = min(size - 1, max(start[1], end[1]) + margin)
    if distance < 10:
        max_iterations = size * size * 2
        timeout = 5.0
    else:
        max_iterations = size * size * 3
        timeout = 10.0
    h_cache = {}
    def h(pos, target, dir_idx=-1):
        cache_key = (pos, target, dir_idx)
        if cache_key in h_cache:
            return h_cache[cache_key]
        basic_dist = abs(pos[0] - target[0]) + abs(pos[1] - target[1])
        turn_estimate = 0
        if with_turning_cost and dir_idx >= 0:
            if target[0] < pos[0]: ideal_dir = 0
            elif target[0] > pos[0]: ideal_dir = 2
            elif target[1] > pos[1]: ideal_dir = 1
            elif target[1] < pos[1]: ideal_dir = 3
            else: ideal_dir = -1
            if ideal_dir != -1 and dir_idx != ideal_dir:
                turn_estimate = 2
        h_value = basic_dist + turn_estimate
        h_cache[cache_key] = h_value
        return h_value
    f_open_set = []
    f_closed_set = set()
    f_g_scores = {}
    f_parents = {}
    f_in_open = set()
    b_open_set = []
    b_closed_set = set()
    b_g_scores = {}
    b_parents = {}
    b_in_open = set()
    iterations = 0
    last_progress_time = time.time()
    f_counter = 0
    b_counter = 0
    if verbose:
        print(f"正在为颜色 {color} 寻找路径: {start} → {end} {'(含转向代价)' if with_turning_cost else ''}")
    f_start_state = encode_state(start[0], start[1], -1)
    f_g_scores[f_start_state] = 0
    f_score = h(start, end, -1)
    heapq.heappush(f_open_set, (f_score, f_counter, f_start_state))
    f_counter += 1
    f_in_open.add(f_start_state)
    b_start_state = encode_state(end[0], end[1], -1)
    b_g_scores[b_start_state] = 0
    b_score = h(end, start, -1)
    heapq.heappush(b_open_set, (b_score, b_counter, b_start_state))
    b_counter += 1
    b_in_open.add(b_start_state)
    best_path_cost = float('inf')
    best_path_meeting_point = None
    best_f_state = None
    best_b_state = None
    while f_open_set and b_open_set:
        iterations += 1
        if iterations > max_iterations or time.time() - start_time > timeout:
            if verbose:
                print(f"颜色 {color} 搜索迭代次数过多({iterations})或超时，停止搜索")
            break
        if verbose and iterations % 1000 == 0 and time.time() - last_progress_time > 1.0:
            elapsed = time.time() - start_time
            print(f"颜色 {color} 搜索进度: 迭代={iterations}, 前向={len(f_closed_set)}, 后向={len(b_closed_set)}, 用时={elapsed:.1f}秒")
            last_progress_time = time.time()
        if f_open_set:
            try:
                _, _, f_current_state = heapq.heappop(f_open_set)
                f_in_open.discard(f_current_state)
                if f_current_state in f_closed_set:
                    continue
                f_x, f_y, f_dir_idx = decode_state(f_current_state)
                f_current = (f_x, f_y)
                if not is_valid_position(f_current, size):
                    continue
                f_closed_set.add(f_current_state)
                for b_dir in range(-1, 4):
                    b_state = encode_state(f_x, f_y, b_dir)
                    if b_state in b_closed_set or b_state in b_in_open:
                        path_cost = f_g_scores[f_current_state] + b_g_scores.get(b_state, float('inf'))
                        if path_cost < best_path_cost:
                            best_path_cost = path_cost
                            best_path_meeting_point = (f_x, f_y)
                            best_f_state = f_current_state
                            best_b_state = b_state
                if f_g_scores[f_current_state] > best_path_cost:
                    continue
                for i, (dx, dy) in enumerate(DIRECTIONS):
                    nx, ny = f_x + dx, f_y + dy
                    neighbor = (nx, ny)
                    if color == 2 or (min_x <= nx <= max_x and min_y <= ny <= max_y):
                        if is_valid_position(neighbor, size):
                            if neighbor == end or neighbor not in occupied_cells:
                                if get_edge(f_current, neighbor) not in used_edges:
                                    turn_cost = 0
                                    if with_turning_cost and f_dir_idx != -1 and f_dir_idx != i:
                                        turn_cost = 2
                                    neighbor_state = encode_state(nx, ny, i)
                                    tentative_g = f_g_scores[f_current_state] + 1 + turn_cost
                                    if neighbor_state not in f_g_scores or tentative_g < f_g_scores[neighbor_state]:
                                        f_parents[neighbor_state] = f_current_state
                                        f_g_scores[neighbor_state] = tentative_g
                                        random_factor = np.random.random() * 0.2 if color == 2 else 0
                                        f_score = tentative_g + h(neighbor, end, i) + random_factor
                                        if neighbor_state not in f_in_open:
                                            heapq.heappush(f_open_set, (f_score, f_counter, neighbor_state))
                                            f_counter += 1
                                            f_in_open.add(neighbor_state)
            except Exception:
                continue
        if b_open_set:
            try:
                _, _, b_current_state = heapq.heappop(b_open_set)
                b_in_open.discard(b_current_state)
                if b_current_state in b_closed_set:
                    continue
                b_x, b_y, b_dir_idx = decode_state(b_current_state)
                b_current = (b_x, b_y)
                if not is_valid_position(b_current, size):
                    continue
                b_closed_set.add(b_current_state)
                for f_dir in range(-1, 4):
                    f_state = encode_state(b_x, b_y, f_dir)
                    if f_state in f_closed_set or f_state in f_in_open:
                        path_cost = b_g_scores[b_current_state] + f_g_scores.get(f_state, float('inf'))
                        if path_cost < best_path_cost:
                            best_path_cost = path_cost
                            best_path_meeting_point = (b_x, b_y)
                            best_f_state = f_state
                            best_b_state = b_current_state
                if b_g_scores[b_current_state] > best_path_cost:
                    continue
                for i, (dx, dy) in enumerate(DIRECTIONS):
                    nx, ny = b_x + dx, b_y + dy
                    neighbor = (nx, ny)
                    if color == 2 or (min_x <= nx <= max_x and min_y <= ny <= max_y):
                        if is_valid_position(neighbor, size):
                            if neighbor == start or neighbor not in occupied_cells:
                                if get_edge(b_current, neighbor) not in used_edges:
                                    turn_cost = 0
                                    if with_turning_cost and b_dir_idx != -1 and b_dir_idx != i:
                                        turn_cost = 2
                                    neighbor_state = encode_state(nx, ny, i)
                                    tentative_g = b_g_scores[b_current_state] + 1 + turn_cost
                                    if neighbor_state not in b_g_scores or tentative_g < b_g_scores[neighbor_state]:
                                        b_parents[neighbor_state] = b_current_state
                                        b_g_scores[neighbor_state] = tentative_g
                                        random_factor = np.random.random() * 0.2 if color == 2 else 0
                                        b_score = tentative_g + h(neighbor, start, i) + random_factor
                                        if neighbor_state not in b_in_open:
                                            heapq.heappush(b_open_set, (b_score, b_counter, neighbor_state))
                                            b_counter += 1
                                            b_in_open.add(neighbor_state)
            except Exception:
                continue
        if best_path_meeting_point is not None and iterations % 100 == 0:
            if (f_open_set and b_open_set and f_open_set[0][0] + b_open_set[0][0] > best_path_cost * 1.1):
                break
    if best_path_meeting_point is None:
        if abs(start[0] - end[0]) + abs(start[1] - end[1]) == 1:
            return [start, end]
        if verbose:
            elapsed = time.time() - start_time
            print(f"颜色 {color} 未找到路径! 迭代={iterations}, 用时={elapsed:.1f}秒")
        return []
    try:
        forward_path = []
        if best_f_state is not None:
            state = best_f_state
            visited_states = set()
            while state in f_parents and state not in visited_states:
                visited_states.add(state)
                x, y, _ = decode_state(state)
                if is_valid_position((x, y), size):
                    forward_path.append((x, y))
                state = f_parents[state]
            if state not in visited_states:
                x, y, _ = decode_state(state)
                if is_valid_position((x, y), size):
                    forward_path.append((x, y))
        forward_path.reverse()
        if not forward_path:
            forward_path = [start]
        elif forward_path[0] != start:
            forward_path[0] = start
        if best_path_meeting_point is not None and (not forward_path or forward_path[-1] != best_path_meeting_point):
            forward_path.append(best_path_meeting_point)
        backward_path = []
        if best_b_state is not None:
            state = best_b_state
            visited_states = set()
            while state in b_parents and state not in visited_states:
                visited_states.add(state)
                x, y, _ = decode_state(state)
                if (x, y) != best_path_meeting_point and is_valid_position((x, y), size):
                    backward_path.append((x, y))
                state = b_parents[state]
            if state not in visited_states:
                x, y, _ = decode_state(state)
                if (x, y) != best_path_meeting_point and is_valid_position((x, y), size):
                    backward_path.append((x, y))
        if not backward_path:
            if end != best_path_meeting_point:
                backward_path = [end]
        elif backward_path[-1] != end:
            backward_path.append(end)
        full_path = forward_path + backward_path
        if len(full_path) < 2:
            full_path = [start, end]
        elif full_path[0] != start or full_path[-1] != end:
            if full_path[0] != start:
                full_path[0] = start
            if full_path[-1] != end:
                full_path[-1] = end
        valid_path = [full_path[0]]
        for i in range(1, len(full_path)):
            prev = valid_path[-1]
            curr = full_path[i]
            if abs(prev[0] - curr[0]) + abs(prev[1] - curr[1]) > 1:
                x_diff = curr[0] - prev[0]
                y_diff = curr[1] - prev[1]
                if abs(x_diff) > 0:
                    step_x = 1 if x_diff > 0 else -1
                    for x in range(prev[0] + step_x, curr[0], step_x):
                        valid_path.append((x, prev[1]))
                if abs(y_diff) > 0:
                    step_y = 1 if y_diff > 0 else -1
                    for y in range(prev[1] + step_y, curr[1] + step_y, step_y):
                        valid_path.append((curr[0], y))
            else:
                valid_path.append(curr)
        elapsed = time.time() - start_time
        if verbose:
            print(f"颜色 {color} 路径找到! 长度={len(valid_path)}, 迭代={iterations}, 用时={elapsed:.1f}秒")
            print(f"路径: {valid_path}")
        return valid_path
    except Exception:
        if best_path_meeting_point is not None:
            simple_path = [start, best_path_meeting_point]
            if best_path_meeting_point != end:
                simple_path.append(end)
            return simple_path
        return [start, end]

def solve_crossline(board: np.ndarray, pairs: Dict[int, List[Tuple[int, int]]], with_turning_cost: bool = False, verbose: bool = True) -> Dict[int, List[Tuple[int, int]]]:
    size = board.shape[0]
    occupied_cells = set()
    total_start_time = time.time()
    for color, positions in pairs.items():
        for pos in positions:
            occupied_cells.add(pos)
    color_paths = {}
    used_cells = occupied_cells.copy()
    used_edges = set()
    if verbose:
        print(f"{'=' * 40}")
        print(f"开始求解 {len(pairs)} 对棋子的连接路径 {'(含转向代价)' if with_turning_cost else ''}")
        print(f"{'=' * 40}")
    pair_distances = []
    for color, positions in pairs.items():
        if len(positions) == 2:
            start, end = positions
            distance = abs(start[0] - end[0]) + abs(start[1] - end[1])
            free_space = 0
            for pos in [start, end]:
                for dx, dy in DIRECTIONS:
                    nx, ny = pos[0] + dx, pos[1] + dy
                    if is_valid_position((nx, ny), size) and (nx, ny) not in occupied_cells:
                        free_space += 1
            if color == 2:
                score = -1000
            else:
                score = distance * 2 - free_space
            pair_distances.append((score, color))
    pair_distances.sort()
    sorted_colors = [color for _, color in pair_distances]
    for idx, color in enumerate(sorted_colors):
        if verbose:
            print(f"\n[{idx+1}/{len(sorted_colors)}] 处理颜色 {color}...")
        if len(pairs[color]) != 2:
            print(f"警告: 颜色 {color} 没有正好2个棋子")
            continue
        start, end = pairs[color]
        try:
            path = bidirectional_astar_search(board, start, end, used_cells - {start, end}, with_turning_cost, color, verbose, used_edges)
            if not path:
                if verbose:
                    print(f"无法为颜色 {color} 找到路径，求解失败")
                return {}
            if len(path) < 2 or path[0] != start or path[-1] != end:
                if verbose:
                    print(f"颜色 {color} 的路径验证失败，起点或终点不匹配")
                    print(f"期望: {start} -> {end}, 实际: {path[0] if path else 'None'} -> {path[-1] if path else 'None'}")
                return {}
            for i in range(1, len(path)):
                if abs(path[i][0] - path[i-1][0]) + abs(path[i][1] - path[i-1][1]) != 1:
                    if verbose:
                        print(f"颜色 {color} 的路径不连续: {path[i-1]} -> {path[i]}")
                    return {}
            for i in range(len(path) - 1):
                edge = get_edge(path[i], path[i+1])
                used_edges.add(edge)
                if path[i] != start and path[i] != end:
                    used_cells.add(path[i])
                if path[i+1] != start and path[i+1] != end:
                    used_cells.add(path[i+1])
            color_paths[color] = path
            if verbose:
                path_cost = get_path_cost(path, with_turning_cost)
                path_length = len(path) - 1
                if with_turning_cost:
                    turn_cost = path_cost - path_length
                    print(f"颜色 {color} 路径完成: 基本长度={path_length}, 转向={turn_cost//2}次, 总代价={path_cost}")
                else:
                    print(f"颜色 {color} 路径完成: 长度={path_cost}")
                print(f"路径结果: {path}")
        except Exception as e:
            if verbose:
                print(f"处理颜色 {color} 时发生错误: {str(e)}")
            return {}
    if verbose:
        total_time = time.time() - total_start_time
        total_cells = 0
        for color, path in color_paths.items():
            start, end = pairs[color]
            for pos in path:
                if pos != start and pos != end:
                    total_cells += 1
        print(f"\n{'=' * 40}")
        print(f"求解完成! 总时间: {total_time:.2f}秒")
        print(f"总共连接了 {len(color_paths)} 对棋子，使用了 {total_cells} 个空格")
        print(f"{'=' * 40}")
    return color_paths

def generate_random_pairs(board_size: int, num_pairs: int, seed: Optional[int] = None) -> Dict[int, List[Tuple[int, int]]]:
    if seed is not None:
        np.random.seed(seed)
    size = board_size
    available_positions = [(i, j) for i in range(size) for j in range(size)]
    pairs = {}
    for color in range(1, num_pairs + 1):
        if len(available_positions) < 2:
            break
        pos_indices = np.random.choice(len(available_positions), 2, replace=False)
        pair_positions = [available_positions[i] for i in pos_indices]
        for idx in sorted(pos_indices, reverse=True):
            available_positions.pop(idx)
        pairs[color] = pair_positions
    return pairs

def validate_board_configuration(board: np.ndarray, pairs: Dict[int, List[Tuple[int, int]]]) -> bool:
    size = board.shape[0]
    for color, positions in pairs.items():
        for pos in positions:
            if not is_valid_position(pos, size):
                print(f"颜色 {color} 的棋子 {pos} 超出棋盘范围")
                return False
    all_positions = []
    for positions in pairs.values():
        all_positions.extend(positions)
    if len(all_positions) != len(set(all_positions)):
        print("存在重叠的棋子")
        return False
    return True