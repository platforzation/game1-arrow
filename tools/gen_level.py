# -*- coding: utf-8 -*-
"""
可解关卡生成器（逆向构造 + 向心方向偏好）：
从空棋盘开始，反复随机放置箭头；每放置一个都用贪心求解器验证
“放置后棋盘仍存在通关顺序”，不满足则回退该放置。
方向按位置偏向棋盘中心（边缘箭头大多朝内被锁住），
使得初始可直接飞出的箭头较少，关卡更有解谜感。

运行方式：python tools/gen_level.py [随机种子]
输出：打印关卡字典（可直接复制进 levels.py）
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game_logic import Board  # noqa: E402

# 向心方向偏好：行在上半偏下(v)、下半偏上(^)、列在左半偏右(>)、右半偏左(<)
CENTER_BIAS = 4          # 指向中心的方向的权重
SIDE_BIAS = 1            # 其他方向的权重


def solvable(grid):
    """贪心求解器：棋盘存在通关顺序则返回 True。"""
    return Board(grid).solve() is not None


def weighted_dir(rows, cols, r, c, rng):
    """按位置返回一个带向心偏好的随机方向（连续权重，方向更均衡）。"""
    dr = r - (rows - 1) / 2.0          # 负=在上半，正=在下半（-0.5~0.5）
    dc = c - (cols - 1) / 2.0          # 负=在左半，正=在右半（-0.5~0.5）
    # 该方向“指向中心”的程度：0~0.5，越大越指向棋盘内部
    toward = {
        '^': max(0.0, dr),             # 在下半则朝上指向中心
        'v': max(0.0, -dr),            # 在上半则朝下指向中心
        '<': max(0.0, dc),             # 在右半则朝左指向中心
        '>': max(0.0, -dc),            # 在左半则朝右指向中心
    }
    w = {d: 1.0 + CENTER_BIAS * toward[d] for d in '^v<>'}
    return rng.choices('^v<>', weights=[w[d] for d in '^v<>'])[0]


def gen_level(rows, cols, target_arrows, rng, max_tries=1200, max_fly=4):
    """
    逆向生成一个 target_arrows 支箭头的可解关卡。
    生成后再做“方向翻转优化”，把初始可直接飞出的箭头数压到 max_fly 以下。
    """
    grid = [['.'] * cols for _ in range(rows)]
    arrows = 0
    tries = 0
    while arrows < target_arrows and tries < max_tries:
        tries += 1
        r = rng.randrange(rows)
        c = rng.randrange(cols)
        if grid[r][c] != '.':
            continue
        ch = weighted_dir(rows, cols, r, c, rng)
        grid[r][c] = ch
        if solvable(grid):
            arrows += 1
        else:
            grid[r][c] = '.'            # 回退：该放置导致死锁

    # ---- 方向翻转优化：压低初始可飞箭头数 ----
    improved = True
    while improved:
        improved = False
        board = Board(grid)
        fly = board.removable_arrows()
        if len(fly) <= max_fly:
            break
        rng.shuffle(fly)
        for (r, c) in fly:
            cur = grid[r][c]
            best, best_n = cur, len(fly)
            for d in '^v<>':
                if d == cur:
                    continue
                grid[r][c] = d
                if solvable(grid):
                    n = len(Board(grid).removable_arrows())
                    if n < best_n:
                        best, best_n = d, n
            grid[r][c] = best
            if best != cur:
                improved = True
    return [''.join(row) for row in grid], arrows


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20260917
    rng = random.Random(seed)
    specs = [          # (rows, cols, 目标箭头数)
        (7, 7, 14),
        (8, 8, 16),
        (9, 9, 18),
        (9, 9, 20),
    ]
    for i, (rows, cols, target) in enumerate(specs, 7):
        grid, arrows = gen_level(rows, cols, target, rng)
        print('第 %d 关（%d×%d，目标 %d 支，实际 %d 支）：' % (
            i, rows, cols, target, arrows))
        for row in grid:
            print('        %r,' % row)
        print()


if __name__ == '__main__':
    main()
