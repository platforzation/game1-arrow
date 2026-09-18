# -*- coding: utf-8 -*-
"""
生成第10关旋转棋盘演示 GIF（短版，约5秒）：
快速消除3个箭头触发第一次旋转，重点录制旋转过程。

运行方式：python tools/make_rotate_gif.py
输出：screenshots/rotate_demo.gif
"""

import os
import sys

os.environ['SDL_VIDEODRIVER'] = 'dummy'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'screenshots')
sys.path.insert(0, ROOT)

import pygame  # noqa: E402
from ui import App, W, H  # noqa: E402
from PIL import Image  # noqa: E402


def main():
    os.makedirs(OUT, exist_ok=True)
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    app = App(screen)
    app.start_level(9)  # 第10关（每消除3个箭头旋转一次）

    frames = []

    def capture():
        app.draw()
        frames.append(pygame.image.tobytes(app.screen, 'RGB', False))

    # 初始画面 20 帧
    for _ in range(20):
        capture()

    # 快速消除 3 个箭头，每步只拍飞出动画+少量停留
    for step in range(3):
        t = app.session.hint()
        if t is None:
            break
        r, c = t
        app.click_cell(r, c)
        # 飞出动画（约 0.34 秒 = 20 帧）
        for _ in range(22):
            app.update(1 / 60)
            capture()
            if not app.animations:
                break
        # 短暂停留 6 帧
        for _ in range(6):
            capture()

    # 第3次消除后应该触发了旋转，旋转动画已在上面捕获
    # 旋转后多拍 25 帧展示新布局
    for _ in range(25):
        capture()

    imgs = [Image.frombytes('RGB', (W, H), f) for f in frames]
    out = os.path.join(OUT, 'rotate_demo.gif')
    imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=33, loop=0)
    print('saved:', os.path.relpath(out, ROOT), '(%d 帧, 约 %.1f 秒)' % (
        len(imgs), len(imgs) * 0.033))
    pygame.quit()


if __name__ == '__main__':
    main()
