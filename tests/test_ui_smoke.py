# -*- coding: utf-8 -*-
"""
UI 冒烟测试：在虚拟显示驱动下运行界面代码，
验证各界面可绘制、点击交互与流程切换不产生运行时错误。
"""

import os
import unittest

os.environ['SDL_VIDEODRIVER'] = 'dummy'

import pygame
from ui import App, W, H, FlyOut, Shake
from game_logic import Session
from levels import LEVELS


class TestUiSmoke(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        pygame.init()
        cls.screen = pygame.display.set_mode((W, H))
        cls.app = App(cls.screen)

    def draw_all_states(self):
        for st in (App.STATE_START, App.STATE_SELECT, App.STATE_GAME,
                   App.STATE_WIN, App.STATE_LOSE, App.STATE_CLEAR):
            self.app.state = st
            self.app.build_buttons()
            self.app.draw()
        self.app.state = App.STATE_GAME

    def test_01_all_screens_draw(self):
        self.app.start_level(0)
        self.draw_all_states()
        # 通关/失败画面在有棋盘内容时也能正常绘制
        self.app.start_level(0)
        self.app.state = App.STATE_WIN
        self.app.build_buttons()
        self.app.draw()

    def test_02_click_unblocked_then_win(self):
        self.app.start_level(0)
        # 跟随提示自动点击，直到通关
        steps = 0
        while self.app.session.status == 'playing' and steps < 50:
            t = self.app.session.hint()
            if t is None:
                break
            self.app.click_cell(*t)
            # 推进飞出动画
            for _ in range(40):
                self.app.update(1 / 60)
                if not self.app.animations:
                    break
            self.app.draw()
            steps += 1
        self.assertEqual(self.app.session.status, 'won')
        self.assertIn(self.app.state, (App.STATE_WIN, App.STATE_CLEAR))

    def test_03_click_blocked_lose_and_restart(self):
        self.app.start_level(0)
        # 找一个被阻挡的箭头，连续点击直到失误耗尽
        for _ in range(6):
            blocked = None
            for r in range(self.app.session.board.rows):
                for c in range(self.app.session.board.cols):
                    if (self.app.session.arrow(r, c)
                            and not self.app.session.board.can_fly(r, c)):
                        blocked = (r, c)
                        break
                if blocked:
                    break
            if not blocked:
                break
            self.app.click_cell(*blocked)
            for _ in range(40):
                self.app.update(1 / 60)
                if self.app.state != App.STATE_GAME:
                    break
            self.app.draw()
        self.assertEqual(self.app.state, App.STATE_LOSE)
        # 重新开始
        self.app.action_restart()
        self.assertEqual(self.app.state, App.STATE_GAME)
        self.assertEqual(self.app.session.mistakes_left, 3)
        self.assertEqual(self.app.session.board.count(), 5)   # 第 1 关共 5 支箭头

    def test_04_level_select_buttons(self):
        self.app.state = App.STATE_SELECT
        self.app.build_buttons()
        self.assertGreaterEqual(len([b for b in self.app.buttons]), len(LEVELS))


if __name__ == '__main__':
    unittest.main()
