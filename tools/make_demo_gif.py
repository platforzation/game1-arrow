# -*- coding: utf-8 -*-
"""
生成演示 GIF：自动求解第 1 关，展示箭头依次飞出的动画效果。

运行方式：python tools/make_demo_gif.py
输出目录：screenshots/demo.gif
"""

import os
import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'screenshots')
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from ui import App, W, H, FlyOut  # noqa: E402
from PIL import Image  # noqa: E402


def main():
    os.makedirs(OUT, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    app = App(screen)
    app.start_level(0)

    frames = []

    def capture():
        app.draw()
        frames.append(pygame.image.tobytes(app.screen, 'RGB', False))

    # 自动游玩：每次点击一个可飞出箭头并播放飞出动画
    guard = 0
    while app.session.status == 'playing' and guard < 80:
        guard += 1
        t = app.session.hint()
        if t is None:
            break
        r, c = t
        ch = app.session.arrow(r, c)
        app.session.click(r, c)
        app.animations.append(FlyOut(r, c, ch, app))
        for _ in range(12):                    # 约 0.4s 的飞出动画
            app.update(1 / 60)
            capture()
            if not app.animations:
                break
        capture()

    # 通关画面收尾
    app.state = App.STATE_WIN
    app.build_buttons()
    for _ in range(8):
        app.draw()
        frames.append(pygame.image.tobytes(app.screen, 'RGB', False))

    imgs = [Image.frombytes('RGB', (W, H), f) for f in frames]
    out = os.path.join(OUT, 'demo.gif')
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=33, loop=0)
    print('saved:', os.path.relpath(out, ROOT), '(%d 帧)' % len(imgs))
    pygame.quit()


if __name__ == '__main__':
    main()
