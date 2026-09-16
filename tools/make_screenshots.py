# -*- coding: utf-8 -*-
"""
生成 README 与博客使用的游戏截图（使用虚拟显示驱动，不会弹出窗口）。

运行方式：python tools/make_screenshots.py
输出目录：screenshots/
"""

import os
import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'screenshots')
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from ui import App, W, H, Shake  # noqa: E402


def shot(app, name):
    path = os.path.join(OUT, name)
    pygame.image.save(app.screen, path)
    print('saved:', os.path.relpath(path, ROOT))


def main():
    os.makedirs(OUT, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    app = App(screen)

    # 1. 开始界面
    app.state = App.STATE_START
    app.build_buttons()
    app.draw()
    shot(app, 'start.png')

    # 2. 关卡选择
    app.state = App.STATE_SELECT
    app.build_buttons()
    app.draw()
    shot(app, 'select.png')

    # 3. 游戏界面（第 1 关）
    app.start_level(0)
    app.draw()
    shot(app, 'game_1.png')

    # 4. 提示高亮
    app.hint_target = app.session.hint()
    app.hint_timer = 0.9
    app.draw()
    shot(app, 'hint.png')
    app.hint_target = None
    app.hint_timer = 0.0

    # 5. 碰撞反馈：点击一个被阻挡的箭头
    blocked = None
    for r in range(app.session.board.rows):
        for c in range(app.session.board.cols):
            if app.session.arrow(r, c) and not app.session.board.can_fly(r, c):
                blocked = (r, c)
                break
        if blocked:
            break
    if blocked:
        r, c = blocked
        ch = app.session.arrow(r, c)
        app.session.click(r, c)                # 失误 -1
        shake = Shake(r, c, ch, app)
        shake.t = 0.14                         # 取晃动进行到一半的画面
        app.animations.append(shake)
        app.draw()
        shot(app, 'collision.png')
        app.animations = []
        app.session.reset()

    # 6. 通关界面（求解器自动清空第 1 关）
    while app.session.status == 'playing':
        t = app.session.hint()
        if t is None:
            break
        app.session.click(*t)
    app.state = App.STATE_WIN
    app.build_buttons()
    app.draw()
    shot(app, 'win.png')

    # 7. 失败界面
    app.state = App.STATE_LOSE
    app.build_buttons()
    app.draw()
    shot(app, 'lose.png')

    # 8. 全部通关界面
    app.state = App.STATE_CLEAR
    app.build_buttons()
    app.draw()
    shot(app, 'clear.png')

    pygame.quit()


if __name__ == '__main__':
    main()
