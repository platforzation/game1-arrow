# -*- coding: utf-8 -*-
"""
一箭又一箭 —— 核心游戏逻辑（与界面无关，便于单元测试）。

箭头方向字符：'^' 上  'v' 下  '<' 左  '>' 右
棋盘用字符串列表表示，例如：
    [
        ">..>",
        ".^..",
        "...v",
        "<...",
    ]
'.' 表示空格。
"""

# 四个方向的行、列偏移
DIRECTIONS = {
    '^': (-1, 0),   # 上
    'v': (1, 0),    # 下
    '<': (0, -1),   # 左
    '>': (0, 1),    # 右
}

DIR_NAMES = {'^': '上', 'v': '下', '<': '左', '>': '右'}

# 顺时针旋转 90° 后的方向映射：上→右，右→下，下→左，左→上
ROTATE_CW = {'^': '>', '>': 'v', 'v': '<', '<': '^'}


class Board:
    """一个关卡的棋盘：rows × cols 的网格，每个格子存放一个方向字符或 None。"""

    def __init__(self, level):
        # type: (list[str]) -> None
        self.rows = len(level)
        self.cols = len(level[0])
        self.grid = [[None] * self.cols for _ in range(self.rows)]
        for r, line in enumerate(level):
            for c, ch in enumerate(line):
                if ch in DIRECTIONS:
                    self.grid[r][c] = ch

    def in_bounds(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols

    def arrow(self, r, c):
        """返回 (r, c) 处的方向字符；越界或空格返回 None。"""
        if not self.in_bounds(r, c):
            return None
        return self.grid[r][c]

    def count(self):
        """当前剩余箭头数量。"""
        return sum(1 for row in self.grid for ch in row if ch is not None)

    def can_fly(self, r, c):
        """
        判断 (r, c) 处的箭头能否飞出：
        沿其方向逐格走到棋盘边界，若路径上没有其他箭头则返回 True。
        """
        ch = self.arrow(r, c)
        if ch is None:
            return False
        dr, dc = DIRECTIONS[ch]
        nr, nc = r + dr, c + dc
        while self.in_bounds(nr, nc):
            if self.grid[nr][nc] is not None:
                return False          # 路径上存在其他箭头，被阻挡
            nr += dr
            nc += dc
        return True                   # 到达边界，畅通无阻

    def removable_arrows(self):
        """返回所有当前可以飞出的箭头坐标列表。"""
        return [(r, c)
                for r in range(self.rows)
                for c in range(self.cols)
                if self.grid[r][c] is not None and self.can_fly(r, c)]

    def clear(self):
        return self.count() == 0

    def rotate_cw(self):
        """
        顺时针旋转棋盘 90°：
        - 行列互换（新尺寸为 cols × rows）；
        - 每个箭头移动到新位置 new_grid[c][rows-1-r]；
        - 箭头方向也顺时针旋转 90°（^→>，>→v，v→<，<→^）。
        旋转是对称变换，箭头间相对阻挡关系不变，关卡可解性保持。
        """
        new_rows, new_cols = self.cols, self.rows
        new_grid = [[None] * new_cols for _ in range(new_rows)]
        for r in range(self.rows):
            for c in range(self.cols):
                ch = self.grid[r][c]
                if ch is not None:
                    nr, nc = c, self.rows - 1 - r
                    new_grid[nr][nc] = ROTATE_CW[ch]
        self.rows, self.cols = new_rows, new_cols
        self.grid = new_grid

    def to_level(self):
        """把当前棋盘状态还原为关卡字符串列表。"""
        return [''.join(ch if ch is not None else '.' for ch in row)
                for row in self.grid]

    def solve(self):
        """
        求解当前关卡：反复删除任意可飞出的箭头。
        由于删除箭头只会移除阻挡、不会新增阻挡，因此贪心顺序即可：
        若某一步没有任何可飞出箭头而棋盘未清空，则本关不可解，返回 None。
        返回删除顺序 [(r, c), ...]。
        """
        order = []
        while not self.clear():
            cands = self.removable_arrows()
            if not cands:
                return None
            r, c = cands[0]
            self.grid[r][c] = None
            order.append((r, c))
        return order


def validate_level(level):
    """
    关卡合法性检查：
    1) 至少 1 行、1 列；
    2) 每行等长，且只包含 '^' 'v' '<' '>' '.'；
    3) 至少包含 1 个箭头；
    4) 可以通过求解器验证（存在通关顺序）。
    返回 (是否合法, 错误信息)。
    """
    if not level or len(level) == 0 or len(level[0]) == 0:
        return False, '关卡为空'
    cols = len(level[0])
    arrow_count = 0
    for line in level:
        if len(line) != cols:
            return False, '各行长度不一致，不是矩形棋盘'
        for ch in line:
            if ch not in '.^v<>':
                return False, '包含非法字符: %r' % ch
            if ch in DIRECTIONS:
                arrow_count += 1
    if arrow_count == 0:
        return False, '关卡中没有箭头'
    board = Board(level)
    if board.solve() is None:
        return False, '该关卡不存在通关顺序（不可解）'
    return True, ''


class Session:
    """一局游戏：棋盘 + 失误次数 + 剩余时间 + 状态机（playing / won / lost），并支持撤销。"""

    def __init__(self, level, max_mistakes=3, time_limit=0, rotate_every=0):
        self.level = [row[:] for row in level]
        self.max_mistakes = max_mistakes
        self.time_limit = time_limit          # 秒；0 表示不限时
        self.rotate_every = rotate_every      # 每消除多少个箭头旋转一次；0 表示不旋转
        self.reset()

    def reset(self):
        """重新开始：棋盘恢复初始布局，失误次数与剩余时间恢复，撤销栈清空。"""
        self.board = Board(self.level)
        self.mistakes_left = self.max_mistakes
        self.time_left = self.time_limit
        self.lose_reason = None               # 失败原因：'mistakes' / 'time'
        self.status = 'playing'      # playing / won / lost
        self.undo_stack = []         # 元素为 (r, c, 方向字符)
        self.removed_count = 0       # 自上次旋转以来已消除的箭头数
        self.just_rotated = False    # 本帧是否刚触发旋转（供 UI 播放动画）

    def rotate_progress(self):
        """距离下次旋转还需消除几个箭头；不旋转的关卡返回 None。"""
        if self.rotate_every <= 0:
            return None
        return self.rotate_every - self.removed_count

    def tick(self, dt):
        """
        推进倒计时（供界面每帧调用）。
        超时则本关失败，返回 True；其余情况返回 False。
        """
        if self.status != 'playing' or self.time_limit <= 0:
            return False
        self.time_left = max(0.0, self.time_left - dt)
        if self.time_left <= 0:
            self.time_left = 0.0
            self.status = 'lost'
            self.lose_reason = 'time'
            return True
        return False

    def click(self, r, c):
        """
        模拟点击棋盘格 (r, c)。
        返回事件类型：
            'none'    —— 空格或游戏已结束，无操作；
            'flew'    —— 箭头飞出并被消除；
            'blocked' —— 前方有阻挡，箭头保留，失误次数 -1。
        """
        if self.status != 'playing':
            return 'none'
        ch = self.arrow(r, c)
        if ch is None:
            return 'none'
        if self.board.can_fly(r, c):
            self.board.grid[r][c] = None
            self.undo_stack.append((r, c, ch))
            self.removed_count += 1
            self.just_rotated = False
            # 达到旋转阈值时顺时针旋转棋盘（旋转后坐标全变，清空撤销栈）
            if self.rotate_every > 0 and self.removed_count >= self.rotate_every \
                    and not self.board.clear():
                self.board.rotate_cw()
                self.undo_stack = []
                self.removed_count = 0
                self.just_rotated = True
            if self.board.clear():
                self.status = 'won'
            return 'flew'
        self.mistakes_left -= 1
        if self.mistakes_left <= 0:
            self.status = 'lost'
            self.lose_reason = 'mistakes'
        return 'blocked'

    def arrow(self, r, c):
        return self.board.arrow(r, c)

    def undo(self):
        """撤销上一次成功的飞出（失误次数不恢复）。返回是否撤销成功。"""
        if self.status != 'playing' or not self.undo_stack:
            return False
        r, c, ch = self.undo_stack.pop()
        self.board.grid[r][c] = ch
        return True

    def hint(self):
        """提示：返回当前任意一个可飞出箭头的坐标；无可飞出箭头返回 None。"""
        if self.status != 'playing':
            return None
        cands = self.board.removable_arrows()
        return cands[0] if cands else None
