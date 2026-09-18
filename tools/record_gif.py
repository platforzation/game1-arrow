# -*- coding: utf-8 -*-
"""
手动录制游戏演示 GIF。

运行方式：python tools/record_gif.py [关卡编号]
  关卡编号从 1 开始，不填默认第 1 关。

操作：
  正常玩游戏；
  按 R 键开始录制（窗口标题会显示 [REC]）；
  再按 R 键停止录制，自动保存为 screenshots/demo_manual.gif；
  按 Esc 返回菜单。

依赖：pip install pillow
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pygame
from ui import App, W, H
from PIL import Image


def main():
    level_idx = 0
    if len(sys.argv) > 1:
        try:
            level_idx = max(0, int(sys.argv[1]) - 1)
        except ValueError:
            pass

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('一箭又一箭 —— 录制模式（按 R 开始/停止录制）')
    app = App(screen)
    app.start_level(level_idx)

    recording = False
    frames = []
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        app.mouse = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    recording = not recording
                    if recording:
                        frames = []
                        pygame.display.set_caption('一箭又一箭 —— [REC] 录制中...（按 R 停止）')
                        print('开始录制...')
                    else:
                        # 保存 GIF
                        out = os.path.join(ROOT, 'screenshots', 'demo_manual.gif')
                        os.makedirs(os.path.dirname(out), exist_ok=True)
                        imgs = [Image.frombytes('RGB', (W, H), f) for f in frames]
                        if imgs:
                            imgs[0].save(out, save_all=True, append_images=imgs[1:],
                                          duration=33, loop=0)
                            print('已保存: %s (%d 帧)' % (out, len(imgs)))
                        frames = []
                        pygame.display.set_caption('一箭又一箭 —— 录制模式（按 R 开始/停止录制）')
                else:
                    app.handle_event(event)
            else:
                app.handle_event(event)

        app.update(dt)
        app.draw()
        pygame.display.flip()

        if recording:
            frames.append(pygame.image.tobytes(screen, 'RGB', False))

    # 退出时如果还在录制，自动保存
    if recording and frames:
        out = os.path.join(ROOT, 'screenshots', 'demo_manual.gif')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        imgs = [Image.frombytes('RGB', (W, H), f) for f in frames]
        imgs[0].save(out, save_all=True, append_images=imgs[1:], duration=33, loop=0)
        print('已保存: %s (%d 帧)' % (out, len(imgs)))

    pygame.quit()


if __name__ == '__main__':
    main()
