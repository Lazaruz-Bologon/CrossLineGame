import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, colorchooser
import numpy as np
import time
import threading
import colorsys
import itertools
from utils import (create_board, add_pairs_to_board, solve_crossline, 
                  get_path_cost, validate_board_configuration)

CELL_SIZE = 50
MARGIN = 20
PIECE_RADIUS = 18
LINE_WIDTH = 4
MAX_COLORS = 20

def generate_colors(n):
    colors = {}
    for i in range(1, n+1):
        hue = (i-1)/n
        r, g, b = colorsys.hsv_to_rgb(hue, 0.8, 0.9)
        hex_color = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
        colors[i] = hex_color
    return colors

class CrossLineUI:
    def __init__(self, root):
        self.root = root
        self.root.title("交叉线连接游戏")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.board_size = tk.IntVar(value=8)
        self.pairs = {}
        self.board = None
        self.paths = None
        self.paths_with_turns = None
        self.current_color = 1
        self.placing_first = True
        self.solving = False
        self.show_turns = tk.BooleanVar(value=False)
        self.detailed_output = tk.BooleanVar(value=True)
        self.grid_visible = tk.BooleanVar(value=True)
        self.auto_retry = tk.BooleanVar(value=True)
        self.colors = generate_colors(MAX_COLORS)
        self._create_widgets()
        self._create_bindings()
        self.reset_board()

    def _create_widgets(self):
        self.root.configure(bg="#f0f0f0")
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        control_frame = ttk.LabelFrame(main_frame, text="控制面板", padding="5")
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        size_frame = ttk.Frame(control_frame)
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(size_frame, text="棋盘大小:").pack(side=tk.LEFT)
        size_spinner = ttk.Spinbox(size_frame, from_=4, to=20, textvariable=self.board_size, width=5)
        size_spinner.pack(side=tk.LEFT, padx=5)
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        reset_button = ttk.Button(button_frame, text="重置棋盘", command=self.reset_board, style="Accent.TButton")
        reset_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        clear_button = ttk.Button(button_frame, text="清空输出", command=self.clear_output)
        clear_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        piece_frame = ttk.LabelFrame(control_frame, text="棋子设置", padding="5")
        piece_frame.pack(fill=tk.X, padx=5, pady=5)
        color_frame = ttk.Frame(piece_frame)
        color_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(color_frame, text="当前颜色:").pack(side=tk.LEFT)
        self.color_label = ttk.Label(color_frame, text="1", width=3)
        self.color_label.pack(side=tk.LEFT, padx=5)
        self.color_canvas = tk.Canvas(color_frame, width=20, height=20, bg=self.colors[1], highlightthickness=1)
        self.color_canvas.pack(side=tk.LEFT, padx=5)
        change_color_btn = ttk.Button(color_frame, text="更换颜色", command=self.change_color, width=10)
        change_color_btn.pack(side=tk.RIGHT)
        button_frame2 = ttk.Frame(piece_frame)
        button_frame2.pack(fill=tk.X, padx=5, pady=5)
        add_pair_button = ttk.Button(button_frame2, text="添加新颜色", command=self.add_new_color)
        add_pair_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        prev_color_button = ttk.Button(button_frame2, text="上一颜色", command=self.prev_color)
        prev_color_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        help_frame = ttk.Frame(piece_frame)
        help_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(help_frame, text="左键放置棋子 | 右键删除棋子", foreground="#555555").pack()
        self.placement_status = ttk.Label(help_frame, text="放置第一个棋子", foreground="#0066cc")
        self.placement_status.pack(fill=tk.X, pady=5)
        options_frame = ttk.LabelFrame(control_frame, text="求解选项", padding="5")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        turn_check = ttk.Checkbutton(options_frame, text="考虑转向代价", variable=self.show_turns)
        turn_check.pack(fill=tk.X, padx=5, pady=5)
        output_check = ttk.Checkbutton(options_frame, text="显示详细输出", variable=self.detailed_output)
        output_check.pack(fill=tk.X, padx=5, pady=5)
        grid_check = ttk.Checkbutton(options_frame, text="显示网格线", variable=self.grid_visible, command=self.draw_board)
        grid_check.pack(fill=tk.X, padx=5, pady=5)
        retry_check = ttk.Checkbutton(options_frame, text="自动尝试所有顺序", variable=self.auto_retry)
        retry_check.pack(fill=tk.X, padx=5, pady=5)
        solve_button = ttk.Button(control_frame, text="求解", command=self.solve_game, style="Accent.TButton")
        solve_button.pack(fill=tk.X, padx=5, pady=10)
        self.style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        progress_frame = ttk.Frame(control_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(progress_frame, text="求解进度:").pack(side=tk.LEFT)
        self.progress_var = tk.StringVar(value="0%")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.pack(side=tk.RIGHT)
        self.progress = ttk.Progressbar(control_frame, orient="horizontal", length=100, mode="determinate")
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        canvas_frame = ttk.LabelFrame(right_frame, text="棋盘视图", padding="5")
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.canvas = tk.Canvas(canvas_frame, background="#ffffff", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        output_frame = ttk.LabelFrame(right_frame, text="输出信息", padding="5")
        output_frame.pack(fill=tk.X, padx=5, pady=5)
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10, font=("Consolas", 10))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.output_text.tag_configure("success", foreground="#009900")
        self.output_text.tag_configure("error", foreground="#cc0000")
        self.output_text.tag_configure("info", foreground="#0066cc")
        self.output_text.tag_configure("header", foreground="#000000", font=("Consolas", 10, "bold"))
        self.output_text.tag_configure("warning", foreground="#FF8C00")

    def _create_bindings(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Button-3>", self.on_canvas_right_click)
        self.canvas.bind("<Configure>", self.draw_board)

    def reset_board(self):
        size = self.board_size.get()
        self.board = create_board(size)
        self.pairs = {}
        self.paths = None
        self.paths_with_turns = None
        self.current_color = 1
        self.placing_first = True
        self.update_color_display()
        self.draw_board()
        self.progress["value"] = 0
        self.progress_var.set("0%")
        self.log("棋盘已重置，大小为 {} x {}".format(size, size), "header")

    def clear_output(self):
        self.output_text.delete(1.0, tk.END)

    def draw_board(self, event=None):
        if self.board is None:
            return
        self.canvas.delete("all")
        size = self.board_size.get()
        if event:
            canvas_width = event.width
            canvas_height = event.height
            board_size = min(canvas_width, canvas_height) - 2 * MARGIN
            self.cell_size = board_size / size
        else:
            self.cell_size = CELL_SIZE
        if self.grid_visible.get():
            for i in range(size + 1):
                y = MARGIN + i * self.cell_size
                self.canvas.create_line(MARGIN, y, MARGIN + size * self.cell_size, y, fill="#DDDDDD")
                x = MARGIN + i * self.cell_size
                self.canvas.create_line(x, MARGIN, x, MARGIN + size * self.cell_size, fill="#DDDDDD")
        else:
            self.canvas.create_rectangle(MARGIN, MARGIN, MARGIN + size * self.cell_size, MARGIN + size * self.cell_size, outline="#AAAAAA")
        if self.show_turns.get() and self.paths_with_turns:
            self.draw_paths(self.paths_with_turns)
        elif self.paths:
            self.draw_paths(self.paths)
        for color, positions in self.pairs.items():
            for pos in positions:
                self.draw_piece(pos, color)

    def draw_piece(self, pos, color):
        x, y = pos
        cx = MARGIN + (x + 0.5) * self.cell_size
        cy = MARGIN + (y + 0.5) * self.cell_size
        piece_radius = min(self.cell_size * 0.4, PIECE_RADIUS)
        self.canvas.create_oval(cx - piece_radius, cy - piece_radius,
                              cx + piece_radius, cy + piece_radius,
                              fill=self.colors.get(color, "#888888"), 
                              outline="#333333",
                              width=2,
                              tags=(f"piece_{x}_{y}", f"color_{color}"))
        self.canvas.create_text(cx, cy, text=str(color), fill="white", 
                              font=("Arial", int(piece_radius*0.8), "bold"),
                              tags=(f"text_{x}_{y}", f"color_{color}"))

    def draw_paths(self, paths):
        for color, path in paths.items():
            if len(path) < 2:
                continue
            color_hex = self.colors.get(color, "#888888")
            for i in range(len(path) - 1):
                x1, y1 = path[i]
                x2, y2 = path[i + 1]
                cx1 = MARGIN + (x1 + 0.5) * self.cell_size
                cy1 = MARGIN + (y1 + 0.5) * self.cell_size
                cx2 = MARGIN + (x2 + 0.5) * self.cell_size
                cy2 = MARGIN + (y2 + 0.5) * self.cell_size
                line_width = max(2, min(LINE_WIDTH, int(self.cell_size * 0.1)))
                self.canvas.create_line(cx1, cy1, cx2, cy2, 
                                      fill=color_hex, 
                                      width=line_width,
                                      capstyle=tk.ROUND,
                                      joinstyle=tk.ROUND,
                                      tags=f"path_{color}")

    def on_canvas_click(self, event):
        if self.solving:
            return
        size = self.board_size.get()
        x = (event.x - MARGIN) / self.cell_size
        y = (event.y - MARGIN) / self.cell_size
        if 0 <= x < size and 0 <= y < size:
            grid_x, grid_y = int(x), int(y)
            self.place_piece((grid_x, grid_y))

    def on_canvas_right_click(self, event):
        if self.solving:
            return
        size = self.board_size.get()
        x = (event.x - MARGIN) / self.cell_size
        y = (event.y - MARGIN) / self.cell_size
        if 0 <= x < size and 0 <= y < size:
            grid_x, grid_y = int(x), int(y)
            self.remove_piece((grid_x, grid_y))

    def remove_piece(self, pos):
        found_color = None
        found_index = -1
        for color, positions in list(self.pairs.items()):
            if pos in positions:
                found_color = color
                found_index = positions.index(pos)
                break
        if found_color is None:
            return
        if len(self.pairs[found_color]) == 1:
            del self.pairs[found_color]
            self.log(f"删除了颜色 {found_color} 的棋子 {pos}", "info")
            if found_color == self.current_color:
                self.placing_first = True
                self.placement_status.config(text=f"颜色 {self.current_color}: 放置第一个棋子")
        else:
            self.pairs[found_color].pop(found_index)
            self.log(f"删除了颜色 {found_color} 的棋子 {pos}", "info")
            if found_color == self.current_color:
                self.placing_first = False
                self.placement_status.config(text=f"颜色 {self.current_color}: 放置第二个棋子")
        self.board = add_pairs_to_board(create_board(self.board_size.get()), self.pairs)
        self.paths = None
        self.paths_with_turns = None
        self.draw_board()

    def place_piece(self, pos):
        for color, positions in self.pairs.items():
            if pos in positions:
                self.log(f"位置 {pos} 已经被棋子占据", "error")
                return
        if self.current_color not in self.pairs:
            self.pairs[self.current_color] = []
        current_pair = self.pairs.get(self.current_color, [])
        if self.placing_first:
            self.pairs[self.current_color] = [pos]
            self.placing_first = False
            self.placement_status.config(text=f"颜色 {self.current_color}: 放置第二个棋子")
            self.log(f"放置颜色 {self.current_color} 的第一个棋子于位置 {pos}", "info")
        else:
            current_pair.append(pos)
            self.pairs[self.current_color] = current_pair
            self.log(f"放置颜色 {self.current_color} 的第二个棋子于位置 {pos}", "info")
            self.current_color += 1
            self.placing_first = True
            self.update_color_display()
            self.placement_status.config(text=f"颜色 {self.current_color}: 放置第一个棋子")
        self.board = add_pairs_to_board(create_board(self.board_size.get()), self.pairs)
        self.paths = None
        self.paths_with_turns = None
        self.draw_board()
        
    def update_color_display(self):
        color = self.current_color
        self.color_label.config(text=str(color))
        self.color_canvas.config(bg=self.colors.get(color, "#888888"))

    def change_color(self):
        color_code = colorchooser.askcolor(initialcolor=self.colors.get(self.current_color, "#888888"))
        if color_code[1]:
            self.colors[self.current_color] = color_code[1]
            self.update_color_display()
            self.draw_board()

    def add_new_color(self):
        if not self.placing_first:
            messagebox.showinfo("提示", "请先放置当前颜色的第二个棋子")
            return
        self.current_color += 1
        if self.current_color > MAX_COLORS:
            self.current_color = 1
        self.update_color_display()
        self.placement_status.config(text=f"颜色 {self.current_color}: 放置第一个棋子")

    def prev_color(self):
        if not self.placing_first:
            messagebox.showinfo("提示", "请先放置当前颜色的第二个棋子")
            return
        self.current_color -= 1
        if self.current_color < 1:
            self.current_color = MAX_COLORS
        self.update_color_display()
        self.placement_status.config(text=f"颜色 {self.current_color}: 放置第一个棋子")
        
    def solve_game(self):
        if not self.pairs:
            messagebox.showinfo("提示", "请先放置棋子")
            return
        incomplete_pairs = [color for color, positions in self.pairs.items() if len(positions) != 2]
        if incomplete_pairs:
            messagebox.showinfo("提示", f"颜色 {incomplete_pairs[0]} 的棋子对不完整，请放置第二个棋子")
            return
        if not validate_board_configuration(self.board, self.pairs):
            messagebox.showerror("错误", "棋盘配置无效")
            return
        self.log("\n开始求解...", "header")
        self.solving = True
        self.progress["value"] = 0
        self.progress_var.set("0%")
        threading.Thread(target=self._solve_in_thread).start()

    def _solve_in_thread(self):
        try:
            verbose = self.detailed_output.get()
            with_turns = self.show_turns.get()
            auto_retry = self.auto_retry.get()
            self.log("\n不考虑转向代价的解:", "header")
            self.paths = None
            if auto_retry:
                colors = list(self.pairs.keys())
                if len(colors) > 8:
                    self.log("棋子对数量过多，使用优化顺序而非尝试所有排列", "warning")
                    start_time = time.time()
                    self.paths = solve_crossline(self.board, self.pairs, False, verbose)
                    time_taken = time.time() - start_time
                    self.root.after(0, lambda: self._display_solution(self.paths, False, time_taken))
                else:
                    permutations = list(itertools.permutations(colors))
                    total = len(permutations)
                    self.log(f"尝试所有可能的连接顺序 (共{total}种排列)", "info")
                    for i, perm in enumerate(permutations):
                        progress = int((i / total) * 100)
                        self.root.after(0, lambda p=progress: self._update_progress(p))
                        self.log(f"\n尝试排列 {i+1}/{total}: {perm}", "info")
                        start_time = time.time()
                        sorted_colors = list(perm)
                        curr_paths = self._try_solve_with_order(sorted_colors, False, verbose)
                        time_taken = time.time() - start_time
                        if curr_paths:
                            self.log("找到有效解决方案!", "success")
                            self.paths = curr_paths
                            self.root.after(0, lambda: self._display_solution(self.paths, False, time_taken))
                            break
                        else:
                            self.log("此顺序无法求解", "warning")
                    if not self.paths:
                        self.log("\n在尝试所有排列后仍未找到解决方案", "error")
                        self.root.after(0, lambda: self._update_progress(100))
            else:
                start_time = time.time()
                self.paths = solve_crossline(self.board, self.pairs, False, verbose)
                time_taken = time.time() - start_time
                self.root.after(0, lambda: self._display_solution(self.paths, False, time_taken))
            if with_turns:
                self.log("\n考虑转向代价的解:", "header")
                self.paths_with_turns = None
                if auto_retry:
                    colors = list(self.pairs.keys())
                    if len(colors) > 8:
                        self.log("棋子对数量过多，使用优化顺序而非尝试所有排列", "warning")
                        start_time = time.time()
                        self.paths_with_turns = solve_crossline(self.board, self.pairs, True, verbose)
                        time_taken = time.time() - start_time
                        self.root.after(0, lambda: self._display_solution(self.paths_with_turns, True, time_taken))
                    else:
                        permutations = list(itertools.permutations(colors))
                        total = len(permutations)
                        self.log(f"尝试所有可能的连接顺序 (考虑转向代价) (共{total}种排列)", "info")
                        for i, perm in enumerate(permutations):
                            progress = int((i / total) * 100)
                            self.root.after(0, lambda p=progress: self._update_progress(p))
                            self.log(f"\n尝试排列 {i+1}/{total}: {perm}", "info")
                            start_time = time.time()
                            sorted_colors = list(perm)
                            curr_paths = self._try_solve_with_order(sorted_colors, True, verbose)
                            time_taken = time.time() - start_time
                            if curr_paths:
                                self.log("找到有效解决方案!", "success")
                                self.paths_with_turns = curr_paths
                                self.root.after(0, lambda: self._display_solution(self.paths_with_turns, True, time_taken))
                                break
                            else:
                                self.log("此顺序无法求解", "warning")
                        if not self.paths_with_turns:
                            self.log("\n在尝试所有排列后仍未找到解决方案 (含转向代价)", "error")
                            self.root.after(0, lambda: self._update_progress(100))
                else:
                    start_time = time.time()
                    self.paths_with_turns = solve_crossline(self.board, self.pairs, True, verbose)
                    time_taken = time.time() - start_time
                    self.root.after(0, lambda: self._display_solution(self.paths_with_turns, True, time_taken))
        except Exception as e:
            self.log(f"求解过程中发生错误: {e}", "error")
        finally:
            self.solving = False
            self.root.after(0, lambda: self._update_progress(100))

    def _try_solve_with_order(self, sorted_colors, with_turning_cost, verbose):
        try:
            from utils import bidirectional_astar_search
            import numpy as np
            board_copy = self.board.copy()
            pairs_copy = {k: v.copy() for k, v in self.pairs.items()}
            size = board_copy.shape[0]
            occupied_cells = set()
            for color, positions in pairs_copy.items():
                for pos in positions:
                    occupied_cells.add(pos)
            used_cells = occupied_cells.copy()
            used_edges = set()
            color_paths = {}
            for idx, color in enumerate(sorted_colors):
                if verbose:
                    self.log(f"[{idx+1}/{len(sorted_colors)}] 处理颜色 {color}...", "info")
                if len(pairs_copy[color]) != 2:
                    self.log(f"警告: 颜色 {color} 没有正好2个棋子", "warning")
                    continue
                start, end = pairs_copy[color]
                path = bidirectional_astar_search(board_copy, start, end, 
                                                used_cells - {start, end}, 
                                                with_turning_cost, color, verbose, used_edges)
                if not path:
                    if verbose:
                        self.log(f"无法为颜色 {color} 找到路径，尝试其他顺序", "warning")
                    return {}
                if len(path) < 2 or path[0] != start or path[-1] != end:
                    if verbose:
                        self.log(f"颜色 {color} 的路径验证失败，起点或终点不匹配", "error")
                    return {}
                for i in range(1, len(path)):
                    if abs(path[i][0] - path[i-1][0]) + abs(path[i][1] - path[i-1][1]) != 1:
                        if verbose:
                            self.log(f"颜色 {color} 的路径不连续: {path[i-1]} -> {path[i]}", "error")
                        return {}
                for i in range(len(path) - 1):
                    x1, y1 = path[i]
                    x2, y2 = path[i+1]
                    if (x1, y1) > (x2, y2):
                        x1, y1, x2, y2 = x2, y2, x1, y1
                    edge = ((x1, y1), (x2, y2))
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
                        self.log(f"颜色 {color} 路径完成: 基本长度={path_length}, 转向={turn_cost//2}次, 总代价={path_cost}", "info")
                    else:
                        self.log(f"颜色 {color} 路径完成: 长度={path_length}", "info")
            return color_paths
        except Exception as e:
            self.log(f"尝试顺序 {sorted_colors} 时出错: {str(e)}", "error")
            return {}

    def _update_progress(self, value):
        self.progress["value"] = value
        self.progress_var.set(f"{value}%")

    def _display_solution(self, paths, with_turns, time_taken):
        if not paths:
            self.log("无法完成所有棋子的连接，求解失败", "error")
            return
        self.log("\n求解结果:", "header")
        total_cells = 0
        for color, path in paths.items():
            basic_cost = len(path) - 1
            total_cost = get_path_cost(path, with_turns)
            if with_turns:
                turn_cost = total_cost - basic_cost
                self.log(f"颜色 {color} 的路径: 基本长度={basic_cost}, 转向={turn_cost//2}次, 总代价={total_cost}", "info")
            else:
                self.log(f"颜色 {color} 的路径长度: {basic_cost}", "info")
            start, end = self.pairs[color]
            for pos in path:
                if pos != start and pos != end:
                    total_cells += 1
        self.log(f"总共连接了 {len(paths)} 对棋子，使用了 {total_cells} 个空格", "success")
        self.log(f"求解耗时: {time_taken:.2f}秒", "info")
        self.draw_board()

    def log(self, message, tag=None):
        self.output_text.insert(tk.END, message + "\n", tag)
        self.output_text.see(tk.END)

def main():
    root = tk.Tk()
    app = CrossLineUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()