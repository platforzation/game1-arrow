# -*- coding: utf-8 -*-
"""
自动化测试：对应作业要求的 T01 ~ T06，另含关卡合法性/可解性测试。

运行方式（项目根目录下）：
    python -m unittest discover -s tests -v
"""

import os
import unittest

# 使用虚拟显示驱动，测试无需弹出真实窗口
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')

from game_logic import Board, Session, validate_level
from levels import LEVELS


class TestT01_UnblockedFly(unittest.TestCase):
    """T01 点击前方无阻挡的箭头：箭头飞出棋盘并消失。"""

    def test_T01_right_unblocked(self):
        s = Session([">.."])            # (0,0) 向右，(0,1)(0,2) 为空
        self.assertEqual(s.click(0, 0), 'flew')
        self.assertIsNone(s.arrow(0, 0), '箭头应被消除')
        self.assertEqual(s.board.count(), 0)

    def test_T01_middle_of_multi(self):
        s = Session([">.>."])           # (0,0) 向右被 (0,2) 阻挡；(0,2) 可飞出
        self.assertEqual(s.click(0, 2), 'flew')
        self.assertIsNone(s.arrow(0, 2))
        self.assertEqual(s.board.count(), 1)
        self.assertEqual(s.status, 'playing')


class TestT02_BlockedClick(unittest.TestCase):
    """T02 点击前方有阻挡的箭头：箭头不消失，失误次数减 1。"""

    def test_T02_blocked(self):
        s = Session([">..<"])           # (0,0) '>' 向右被 (0,3) '<' 阻挡
        self.assertEqual(s.click(0, 0), 'blocked')
        self.assertEqual(s.arrow(0, 0), '>', '被阻挡的箭头不应消失')
        self.assertEqual(s.mistakes_left, 2, '失误次数应减 1')
        self.assertEqual(s.status, 'playing')

    def test_T02_blocked_keeps_count(self):
        # (1,0) '>' 向右路径为空，不受 (0,0) '<' 影响（不同行不构成阻挡）
        s = Session(["<.>", ">.."], max_mistakes=3)
        self.assertEqual(s.click(1, 0), 'flew')
        self.assertEqual(s.mistakes_left, 3)


class TestT03_EdgeOutward(unittest.TestCase):
    """T03 点击位于边缘且朝向棋盘外的箭头：正常消失，不发生越界错误。"""

    def test_T03_top_up_arrow(self):
        # (0,0) 位于顶边且朝上，即使下方有箭头也不应被阻挡
        s = Session(["^", "v"])
        self.assertEqual(s.click(0, 0), 'flew', '顶边向上的箭头应可飞出')
        self.assertIsNone(s.arrow(0, 0))

    def test_T03_bottom_down_arrow(self):
        s = Session(["^", "v"])
        self.assertEqual(s.click(1, 0), 'flew', '底边向下的箭头应可飞出')

    def test_T03_left_right_outward(self):
        s = Session(["<.>"])
        self.assertEqual(s.click(0, 0), 'flew', '左边向左的箭头应可飞出')
        self.assertEqual(s.click(0, 2), 'flew', '右边向右的箭头应可飞出')

    def test_T03_corner(self):
        s = Session(["^.", ".<"])       # 左上角朝上、右下角朝左均指向边界外
        self.assertEqual(s.click(0, 0), 'flew')
        self.assertEqual(s.click(1, 1), 'flew')


class TestT04_LevelClear(unittest.TestCase):
    """T04 消除本关全部箭头：显示通关并进入下一关。"""

    def test_T04_clear_all_wins(self):
        s = Session(LEVELS[0]['grid'], LEVELS[0]['max_mistakes'])
        # 反复点“提示”给出的可飞出箭头，直到清空
        while s.status == 'playing':
            target = s.hint()
            self.assertIsNotNone(target, '可解关卡每一步都应有可飞出箭头')
            r, c = target
            self.assertEqual(s.click(r, c), 'flew')
        self.assertEqual(s.status, 'won', '清空全部箭头后应通关')
        self.assertEqual(s.board.count(), 0)

    def test_T04_next_level_exists(self):
        self.assertGreaterEqual(len(LEVELS), 3, '至少应有 3 个关卡')
        # 最后一关通关后应能回到菜单或提示全部通关（LEVELS 数量满足要求即可）


class TestT05_MistakesExhausted(unittest.TestCase):
    """T05 失误次数耗尽：显示失败并允许重新开始。"""

    def test_T05_lost_when_zero(self):
        s = Session(["><"], max_mistakes=1)   # (0,0) '>' 被 (0,1) '<' 阻挡
        self.assertEqual(s.click(0, 0), 'blocked')
        self.assertEqual(s.mistakes_left, 0)
        self.assertEqual(s.status, 'lost', '失误耗尽后应失败')

    def test_T05_restart_after_lost(self):
        s = Session(["><"], max_mistakes=1)
        s.click(0, 0)
        s.reset()
        self.assertEqual(s.status, 'playing', '重新开始后应回到进行中')
        self.assertEqual(s.mistakes_left, 1, '失误次数应恢复')
        self.assertEqual(s.arrow(0, 0), '>', '棋盘布局应恢复初始状态')


class TestT06_RestartMidGame(unittest.TestCase):
    """T06 游戏进行中重新开始：箭头布局和失误次数恢复。"""

    def test_T06_restart_mid_game(self):
        # ".<>..>"：(0,1) '<' 向左无阻挡可飞出；(0,2) '>' 向右被 (0,5) '>' 阻挡
        s = Session([".<>..>"], max_mistakes=2)
        s.click(0, 1)                       # 先成功飞出 1 个箭头
        s.click(0, 2)                       # 再点击被阻挡箭头，失误 1 次
        self.assertEqual(s.board.count(), 2)
        self.assertEqual(s.mistakes_left, 1)
        s.reset()
        self.assertEqual(s.board.count(), 3, '重新开始后箭头布局应恢复')
        self.assertEqual(s.mistakes_left, 2, '重新开始后失误次数应恢复')
        self.assertEqual(s.status, 'playing')
        self.assertEqual(s.undo_stack, [], '重新开始后撤销栈应清空')


class TestT07_TimeLimit(unittest.TestCase):
    """T07 时间限制：倒计时递减、超时判负、失败原因区分、重开恢复。"""

    def test_T07_countdown_decreases(self):
        s = Session([">.."], max_mistakes=3, time_limit=60)
        self.assertEqual(s.time_left, 60)
        s.tick(10)
        self.assertAlmostEqual(s.time_left, 50)
        self.assertEqual(s.status, 'playing', '时间未到不应失败')

    def test_T07_timeout_loses(self):
        s = Session([">.."], max_mistakes=3, time_limit=5)
        s.tick(5.1)
        self.assertEqual(s.status, 'lost', '超时应判失败')
        self.assertEqual(s.lose_reason, 'time', '失败原因应为时间耗尽')
        self.assertEqual(s.time_left, 0.0)

    def test_T07_mistake_lose_reason(self):
        s = Session(["><"], max_mistakes=1, time_limit=60)
        s.click(0, 0)
        self.assertEqual(s.status, 'lost')
        self.assertEqual(s.lose_reason, 'mistakes', '失败原因应为失误耗尽')

    def test_T07_no_limit_ignores_tick(self):
        s = Session([">.."])               # 默认不限时
        s.tick(999)
        self.assertEqual(s.status, 'playing')
        self.assertEqual(s.time_left, 0)

    def test_T07_restart_resets_time(self):
        s = Session([">.."], max_mistakes=3, time_limit=30)
        s.tick(10)
        s.reset()
        self.assertEqual(s.time_left, 30, '重新开始后剩余时间应恢复')

    def test_T07_won_stops_countdown(self):
        s = Session([">.."], max_mistakes=3, time_limit=30)
        s.click(0, 0)                      # 通关
        s.tick(60)
        self.assertEqual(s.status, 'won', '通关后不应再超时')
        self.assertEqual(s.lose_reason, None)

    def test_T07_time_not_consumed_by_mistakes(self):
        s = Session(["><"], max_mistakes=3, time_limit=30)
        s.click(0, 0)                      # 失误一次
        s.tick(5)
        self.assertAlmostEqual(s.time_left, 25, '失误不消耗时间，时间只随 tick 减少')


class TestLevelValidity(unittest.TestCase):
    """所有关卡：格式合法且存在通关顺序（防止提交不可通关的关卡）。"""

    def test_levels_are_valid_and_solvable(self):
        self.assertGreaterEqual(len(LEVELS), 3)
        for i, lv in enumerate(LEVELS, 1):
            ok, msg = validate_level(lv['grid'])
            self.assertTrue(ok, '第 %d 关不合法或不可解：%s' % (i, msg))
            self.assertGreater(lv['max_mistakes'], 0)

    def test_unsolvable_level_detected(self):
        # 互堵死锁关卡：两箭头互相阻挡，应被求解器判为不可解
        deadlock = [
            ">...<",
            ".....",
            ".....",
        ]
        ok, _ = validate_level(deadlock)
        self.assertFalse(ok, '互堵关卡应被判定为不可解')


if __name__ == '__main__':
    unittest.main()
