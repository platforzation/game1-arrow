# -*- coding: utf-8 -*-
"""
关卡验证工具：逐个关卡检查
  1) 格式合法（矩形、字符合法、含箭头）；
  2) 存在通关顺序（贪心求解器）；
  3) 输出棋盘尺寸、箭头数量与一个可行解的长度。

运行方式：python tools/validate_levels.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from game_logic import Board, validate_level  # noqa: E402
from levels import LEVELS  # noqa: E402


def main():
    print('%-22s %-10s %-8s %-8s %-10s %-14s %s' % (
        '关卡', '棋盘', '箭头数', '限时(s)', '失误上限', '初始可飞', '可解'))
    print('-' * 88)
    all_ok = True
    for i, lv in enumerate(LEVELS, 1):
        grid = lv['grid']
        ok, msg = validate_level(grid)
        rows, cols = len(grid), len(grid[0])
        n = sum(1 for row in grid for ch in row if ch in '^v<>')
        solve_len = '-'
        init_fly = '-'
        if ok:
            b = Board(grid)
            init_fly = len(b.removable_arrows())
            order = b.solve()
            solve_len = len(order) if order else '-'
        else:
            all_ok = False
        print('%-22s %-10s %-8d %-8s %-10s %-14s %s' % (
            lv['name'], '%d×%d' % (rows, cols), n,
            lv.get('time_limit', '不限'), lv['max_mistakes'],
            init_fly,
            '✓（解长 %s）' % solve_len if ok else '✗ %s' % msg))
    print('-' * 88)
    print('全部关卡可解：%s' % ('是' if all_ok else '否，请调整关卡！'))
    return 0 if all_ok else 1


if __name__ == '__main__':
    sys.exit(main())
