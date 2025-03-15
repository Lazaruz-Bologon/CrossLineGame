from utils import (create_board, add_pairs_to_board, visualize_board, 
                   get_path_cost, solve_crossline)
import argparse
import time

def parse_pair(pair_str):
    try:
        parts = pair_str.strip().split('-')
        if len(parts) != 2:
            raise ValueError("棋子对格式错误，应为'x1,y1-x2,y2'")
        start = tuple(map(int, parts[0].split(',')))
        end = tuple(map(int, parts[1].split(',')))
        if len(start) != 2 or len(end) != 2:
            raise ValueError("坐标格式错误，应为'x,y'")
        return [start, end]
    except Exception as e:
        print(f"解析错误: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="交叉线游戏求解器")
    parser.add_argument("--size", type=int, default=8, help="棋盘大小")
    parser.add_argument("--pairs", type=str, nargs="+", help="棋子对，格式: '色号:x1,y1-x2,y2'")
    parser.add_argument("--turning_cost", action="store_true", help="是否考虑转向代价")
    parser.add_argument("--quiet", action="store_true", help="安静模式，不显示详细进度")
    args = parser.parse_args()
    verbose = not args.quiet
    board = create_board(args.size)
    pairs = {}
    if args.pairs:
        for pair_str in args.pairs:
            try:
                color, positions = pair_str.split(":", 1)
                color = int(color)
                positions = parse_pair(positions)
                if positions:
                    pairs[color] = positions
            except ValueError as e:
                print(f"解析棋子对失败: {e}")
                return
    else:
        pairs = {
            1: [(0, 0), (3, 3)],
            2: [(1, 1), (2, 3)],
            3: [(2, 2), (3, 0)]
        }
    board = add_pairs_to_board(board, pairs)
    print("初始棋盘:")
    visualize_board(board)
    print("不考虑转向代价的解:")
    start_time = time.time()
    paths = solve_crossline(board, pairs, False, verbose)
    time_taken = time.time() - start_time
    if not paths:
        print("无法完成所有棋子的连接，求解失败")
    else:
        visualize_board(board, paths)
        for color, path in paths.items():
            cost = get_path_cost(path, False)
            print(f"颜色 {color} 的路径长度: {cost}")
        print(f"求解耗时: {time_taken:.2f}秒")
    print("\n考虑转向代价的解:")
    start_time = time.time()
    paths_with_turn = solve_crossline(board, pairs, True, verbose)
    time_taken = time.time() - start_time
    if not paths_with_turn:
        print("无法完成所有棋子的连接，求解失败")
    else:
        visualize_board(board, paths_with_turn)
        for color, path in paths_with_turn.items():
            basic_cost = len(path) - 1
            total_cost = get_path_cost(path, True)
            turn_cost = total_cost - basic_cost
            print(f"颜色 {color} 的路径: 基本长度={basic_cost}, 转向代价={turn_cost}, 总代价={total_cost}")
        print(f"求解耗时: {time_taken:.2f}秒")

def interactive_mode():
    try:
        size = int(input("请输入棋盘大小: "))
        verbose = input("是否显示详细进度? (y/n): ").lower().startswith('y')
        board = create_board(size)
        pairs = {}
        num_pairs = int(input("请输入棋子对数量: "))
        for i in range(1, num_pairs + 1):
            print(f"\n添加第{i}对棋子:")
            color = i
            try:
                x1, y1 = map(int, input(f"请输入颜色{color}的第一个棋子坐标 (x,y): ").split(","))
                x2, y2 = map(int, input(f"请输入颜色{color}的第二个棋子坐标 (x,y): ").split(","))
                if not (0 <= x1 < size and 0 <= y1 < size and 0 <= x2 < size and 0 <= y2 < size):
                    print("坐标超出范围，请重新输入")
                    i -= 1
                    continue
                pairs[color] = [(x1, y1), (x2, y2)]
            except ValueError:
                print("输入格式错误，请使用逗号分隔x,y坐标")
                i -= 1
                continue
        board = add_pairs_to_board(board, pairs)
        print("\n初始棋盘:")
        visualize_board(board)
        print("\n不考虑转向代价的解:")
        start_time = time.time()
        paths = solve_crossline(board, pairs, False, verbose)
        time_taken = time.time() - start_time
        if not paths:
            print("无法完成所有棋子的连接，求解失败")
        else:
            visualize_board(board, paths)
            for color, path in paths.items():
                cost = get_path_cost(path, False)
                print(f"颜色 {color} 的路径长度: {cost}")
            print(f"求解耗时: {time_taken:.2f}秒")
        print("\n考虑转向代价的解:")
        start_time = time.time()
        paths_with_turn = solve_crossline(board, pairs, True, verbose)
        time_taken = time.time() - start_time
        if not paths_with_turn:
            print("无法完成所有棋子的连接，求解失败")
        else:
            visualize_board(board, paths_with_turn)
            for color, path in paths_with_turn.items():
                basic_cost = len(path) - 1
                total_cost = get_path_cost(path, True)
                turn_cost = total_cost - basic_cost
                print(f"颜色 {color} 的路径: 基本长度={basic_cost}, 转向代价={turn_cost}, 总代价={total_cost}")
            print(f"求解耗时: {time_taken:.2f}秒")
    except ValueError as e:
        print(f"输入错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        main()
    else:
        interactive_mode()