# -*- coding: utf-8 -*-
"""
一箭又一箭 —— Pygame 图形界面。

包含：开始界面、关卡选择、游戏界面（棋盘 + HUD）、通关/失败/全部通关界面，
以及箭头飞出、碰撞晃动、提示高亮等动画与视觉反馈。
"""

import math
import os
import sys

import pygame

from game_logic import Session, DIRECTIONS, DIR_NAMES
from levels import LEVELS

# ---------------- 常量 ----------------
W, H = 880, 700          # 窗口尺寸
HUD_H = 110              # 顶部信息栏高度
CELL = 76                # 棋盘格边长（大棋盘会按行列数自适应缩小）
FPS = 60

# 配色
PAPER = (247, 243, 232)        # 棋盘底色（暖纸色）
GRID_LINE = (216, 207, 186)    # 网格线
INK = (56, 52, 46)             # 深色文字
SUB_INK = (126, 118, 104)      # 次要文字
ARROW_BLUE = (74, 118, 190)    # 箭头主体
ARROW_DARK = (38, 66, 118)     # 箭头描边
ARROW_GOLD = (226, 168, 62)    # 飞出时的箭头
BLOCKED_RED = (208, 72, 66)    # 碰撞时的箭头
HINT_YELLOW = (250, 200, 70)   # 提示光圈
HUD_BG = (236, 229, 211)
BTN_BLUE = (74, 118, 190)
BTN_HOVER = (100, 148, 222)
BTN_BORDER = (30, 52, 92)
BTN_TEXT = (255, 255, 255)
OVERLAY = (0, 0, 0, 150)

# 中文字体候选（Windows 常见字体，依次尝试）
# 注意：不使用 pygame.font.match_font()——官方 pygame 2.6.x 在 Windows 上
# 扫描系统字体时有 bug（TypeError: expected str... not int），直接读字体文件路径最稳。
FONT_DIR = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')
# (常规, 粗体) 候选字体文件名，按优先级排列
FONT_FILES = [
    ('msyh.ttc', 'msyhbd.ttc'),    # 微软雅黑
    ('simhei.ttf', 'simhei.ttf'),  # 黑体（没有单独粗体文件，用同一文件）
    ('Deng.ttf', 'Deng.ttf'),      # 等线
    ('simsun.ttc', 'simsun.ttc'),  # 宋体
    ('simkai.ttf', 'simkai.ttf'),  # 楷体
]


def get_font(size, bold=False):
    """获取支持中文的字体；直接读 Windows 字体文件，绕过 match_font 的 bug。"""
    for regular, bold_file in FONT_FILES:
        fname = bold_file if bold else regular
        path = os.path.join(FONT_DIR, fname)
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue
    return pygame.font.Font(None, size)


def fmt_time(sec):
    """把秒数格式化为 MM:SS（向上取整，保证显示 1 秒时剩余 1 秒）。"""
    sec = int(math.ceil(max(0.0, sec)))
    return '%02d:%02d' % (sec // 60, sec % 60)



def draw_arrow(surf, center, direction, size, color, dark, alpha=255):
    """在 center 处绘制一个 direction 方向的箭头，size 为整体像素尺寸。"""
    size = int(size)
    tmp = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
    cx = cy = size
    # 以“向右”为基准图形：尾杆 + 箭头
    tail = pygame.Rect(cx - size * 0.42, cy - size * 0.10, size * 0.42, size * 0.20)
    head = [
        (cx + size * 0.20, cy),
        (cx - size * 0.30, cy + size * 0.36),
        (cx - size * 0.30, cy - size * 0.36),
    ]
    pygame.draw.rect(tmp, dark, tail.move(1, 1), border_radius=size // 6)
    pygame.draw.polygon(tmp, dark, [(x + 1, y + 1) for x, y in head])
    pygame.draw.rect(tmp, color, tail, border_radius=size // 6)
    pygame.draw.polygon(tmp, color, head)
    # pygame.transform.rotate 正角度为逆时针；基准图形朝右，故：
    # 朝右=0°，朝上=90°，朝左=180°，朝下=270°
    angle = {'>': 0, '^': 90, '<': 180, 'v': 270}[direction]
    if angle:
        tmp = pygame.transform.rotate(tmp, angle)
    tmp.set_alpha(alpha)
    surf.blit(tmp, (center[0] - tmp.get_width() // 2, center[1] - tmp.get_height() // 2))


class Button:
    """带悬停效果的圆角按钮。"""

    def __init__(self, rect, text, action, font=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.action = action
        self.font = font or get_font(22)
        self.hover = False

    def draw(self, surf, mouse):
        self.hover = self.rect.collidepoint(mouse)
        color = BTN_HOVER if self.hover else BTN_BLUE
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        pygame.draw.rect(surf, BTN_BORDER, self.rect, width=2, border_radius=12)
        img = self.font.render(self.text, True, BTN_TEXT)
        surf.blit(img, img.get_rect(center=self.rect.center))


class LevelButton(Button):
    """关卡选择按钮：显示关卡名 + 箭头数量。"""

    def __init__(self, rect, name, count, action):
        super().__init__(rect, name, action, get_font(20, bold=True))
        self.count = count

    def draw(self, surf, mouse):
        self.hover = self.rect.collidepoint(mouse)
        color = BTN_HOVER if self.hover else BTN_BLUE
        pygame.draw.rect(surf, color, self.rect, border_radius=12)
        pygame.draw.rect(surf, BTN_BORDER, self.rect, width=2, border_radius=12)
        img = self.font.render(self.text, True, BTN_TEXT)
        surf.blit(img, img.get_rect(center=(self.rect.centerx, self.rect.centery - 16)))
        sub = get_font(15).render('共 %d 支箭头' % self.count, True, (225, 232, 244))
        surf.blit(sub, sub.get_rect(center=(self.rect.centerx, self.rect.centery + 20)))


# ---------------- 动画 ----------------

class FlyOut:
    """箭头飞出动画：从原格滑向棋盘外一格，逐渐淡出。"""

    def __init__(self, r, c, ch, app):
        self.app = app
        self.r, self.c, self.ch = r, c, ch
        self.t = 0.0
        self.dur = 0.34
        dr, dc = DIRECTIONS[ch]
        self.start = app.cell_center(r, c)
        self.end = app.cell_center(r + dr, c + dc)   # 棋盘外一格

    def update(self, dt):
        self.t += dt
        return self.t >= self.dur

    def draw(self, surf):
        k = min(1.0, self.t / self.dur)
        pos = (self.start[0] + (self.end[0] - self.start[0]) * k,
               self.start[1] + (self.end[1] - self.start[1]) * k)
        alpha = 255 if k < 0.6 else int(255 * (1 - k) / 0.4)
        draw_arrow(surf, pos, self.ch, self.app.cell * 0.55, ARROW_GOLD, (140, 96, 30), alpha)


class Shake:
    """碰撞反馈动画：箭头左右晃动并变红，提示前方有阻挡。"""

    def __init__(self, r, c, ch, app):
        self.app = app
        self.r, self.c, self.ch = r, c, ch
        self.t = 0.0
        self.dur = 0.45

    def update(self, dt):
        self.t += dt
        return self.t >= self.dur

    def draw(self, surf):
        k = self.t / self.dur
        off = math.sin(self.t * 42) * 6 * (1 - k)
        pos = self.app.cell_center(self.r, self.c)
        draw_arrow(surf, (pos[0] + off, pos[1]), self.ch, self.app.cell * 0.55,
                   BLOCKED_RED, (130, 40, 36))


class FloatText:
    """上升并淡出的提示文字（如“前方有阻挡！”“时间到！”）。"""

    def __init__(self, text, pos, color=BLOCKED_RED, cell=CELL):
        self.text = text
        self.pos = pos
        self.color = color
        self.cell = cell
        self.t = 0.0
        self.dur = 0.9

    def update(self, dt):
        self.t += dt
        return self.t >= self.dur

    def draw(self, surf):
        k = self.t / self.dur
        alpha = 255 if k < 0.5 else int(255 * (1 - k) / 0.5)
        img = get_font(24, bold=True).render(self.text, True, self.color)
        img.set_alpha(alpha)
        y = self.pos[1] - self.cell - 8 - k * 26
        surf.blit(img, img.get_rect(center=(self.pos[0], y)))


class BoardRotate:
    """棋盘旋转动画：旋转前的棋盘截图旋转 90° 并缩小淡出，露出旋转后的新布局。"""

    def __init__(self, app, before_surface):
        self.app = app
        self.before = before_surface
        self.t = 0.0
        self.dur = 0.6

    def update(self, dt):
        self.t += dt
        return self.t >= self.dur

    def draw(self, surf):
        k = min(1.0, self.t / self.dur)
        angle = 90 * k
        scale = max(0.1, 1.0 - 0.9 * k)
        alpha = int(255 * (1 - k))
        if alpha <= 0:
            return
        tmp = pygame.transform.rotozoom(self.before, angle, scale)
        tmp.set_alpha(alpha)
        bx, by = self.app.board_origin()
        cx = bx + self.app.session.board.cols * self.app.cell // 2
        cy = by + self.app.session.board.rows * self.app.cell // 2
        surf.blit(tmp, tmp.get_rect(center=(cx, cy)))


# ---------------- 主应用 ----------------

class App:
    STATE_START = 'start'
    STATE_SELECT = 'select'
    STATE_GAME = 'game'
    STATE_WIN = 'win'
    STATE_LOSE = 'lose'
    STATE_CLEAR = 'clear'

    def __init__(self, screen):
        pygame.init()
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.mouse = (0, 0)
        self.state = self.STATE_START
        self.level_index = 0
        self.session = None
        self.cell = CELL              # 当前关卡格子边长（大棋盘自适应缩小）
        self.animations = []      # FlyOut / Shake
        self.floats = []          # FloatText
        self.hint_target = None   # 提示高亮的箭头坐标
        self.hint_timer = 0.0
        self.buttons = []
        self._lose_timer = None   # 失败画面的延迟显示计时
        self.build_buttons()

    # ---------- 几何换算 ----------

    def board_origin(self):
        rows = self.session.board.rows if self.session else 4
        cols = self.session.board.cols if self.session else 4
        bx = (W - cols * self.cell) // 2
        by = HUD_H + (H - HUD_H - rows * self.cell) // 2
        return bx, by

    def cell_center(self, r, c):
        bx, by = self.board_origin()
        return (bx + c * self.cell + self.cell // 2,
                by + r * self.cell + self.cell // 2)

    def cell_at(self, x, y):
        bx, by = self.board_origin()
        r = (y - by) // self.cell
        c = (x - bx) // self.cell
        if 0 <= r < self.session.board.rows and 0 <= c < self.session.board.cols:
            return int(r), int(c)
        return None

    def capture_board(self):
        """把当前棋盘（含背景、网格、箭头）绘制到独立 Surface 并返回，供旋转动画使用。"""
        b = self.session.board
        cell = self.cell
        pad = 10
        w = b.cols * cell + pad * 2
        h = b.rows * cell + pad * 2
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (240, 235, 221), (0, 0, w, h), border_radius=12)
        for r in range(b.rows):
            for c in range(b.cols):
                rect = pygame.Rect(pad + c * cell, pad + r * cell, cell, cell)
                pygame.draw.rect(surf, GRID_LINE, rect, width=1)
        for r in range(b.rows):
            for c in range(b.cols):
                ch = b.arrow(r, c)
                if ch is not None:
                    cx = pad + c * cell + cell // 2
                    cy = pad + r * cell + cell // 2
                    draw_arrow(surf, (cx, cy), ch, cell * 0.55, ARROW_BLUE, ARROW_DARK)
        return surf

    # ---------- 流程控制 ----------

    def start_level(self, i):
        """进入第 i 关（i 从 0 开始）。"""
        self.level_index = i
        lv = LEVELS[i]
        self.session = Session(lv['grid'], lv['max_mistakes'],
                               lv.get('time_limit', 0),
                               lv.get('rotate_every', 0))
        # 大棋盘自适应缩小格子，保证整个棋盘居中显示
        rows, cols = self.session.board.rows, self.session.board.cols
        self.cell = max(40, min(CELL, (W - 60) // cols, (H - HUD_H - 60) // rows))
        self.animations = []
        self.floats = []
        self.hint_target = None
        self.hint_timer = 0.0
        self._lose_timer = None
        self.state = self.STATE_GAME
        self.build_buttons()

    def action_start(self):
        self.start_level(0)

    def action_select(self):
        self.state = self.STATE_SELECT
        self.build_buttons()

    def action_level(self, i):
        self.start_level(i)

    def action_restart(self):
        """重新开始当前关卡。"""
        if self.session:
            self.session.reset()
            self.animations = []
            self.floats = []
            self.hint_target = None
            self.hint_timer = 0.0
            self._lose_timer = None
            self.state = self.STATE_GAME
            self.build_buttons()

    def action_hint(self):
        """提示：高亮一个当前可以飞出的箭头。"""
        if self.session:
            t = self.session.hint()
            if t:
                self.hint_target = t
                self.hint_timer = 1.6

    def action_undo(self):
        """撤销上一次成功的飞出。"""
        if self.session:
            self.session.undo()
            self.animations = []

    def action_next(self):
        if self.level_index + 1 < len(LEVELS):
            self.start_level(self.level_index + 1)
        else:
            self.state = self.STATE_CLEAR
            self.build_buttons()

    def action_start_menu(self):
        self.state = self.STATE_START
        self.build_buttons()

    def action_quit(self):
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def click_cell(self, r, c):
        """点击棋盘格：判定并播放飞出或碰撞反馈。"""
        if self.state != self.STATE_GAME or not self.session:
            return
        if self.session.status != 'playing':
            return
        ch = self.session.arrow(r, c)
        if ch is None:
            return
        # 该箭头正在播放碰撞晃动动画时，忽略重复点击（防止快速连点重复扣失误）
        if any(isinstance(a, Shake) and a.r == r and a.c == c for a in self.animations):
            return
        # 棋盘旋转动画期间忽略点击
        if any(isinstance(a, BoardRotate) for a in self.animations):
            return
        if self.session.board.can_fly(r, c):
            # 判断本次消除后是否会触发棋盘旋转
            will_rotate = (self.session.rotate_every > 0
                           and self.session.removed_count + 1 >= self.session.rotate_every
                           and self.session.board.count() > 1)
            if will_rotate:
                # 先捕获旋转前的棋盘截图，再执行消除+旋转
                before_surf = self.capture_board()
                self.session.click(r, c)
                if self.session.just_rotated:
                    self.animations.append(BoardRotate(self, before_surf))
                    self.floats.append(FloatText('棋盘旋转！', (W // 2, H // 2),
                                                 color=ARROW_GOLD, cell=self.cell))
            else:
                self.session.click(r, c)
                self.animations.append(FlyOut(r, c, ch, self))
        else:
            self.session.click(r, c)          # 被阻挡：失误次数 -1
            self.animations.append(Shake(r, c, ch, self))
            self.floats.append(FloatText('前方有阻挡！', self.cell_center(r, c),
                                         cell=self.cell))
            if self.session.status == 'lost':
                self._lose_timer = 0.6        # 稍作延迟，让晃动反馈可见

    # ---------- 按钮布局 ----------

    def build_buttons(self):
        self.buttons = []
        b = self.buttons.append
        if self.state == self.STATE_START:
            b(Button((W // 2 - 130, 392, 260, 54), '开始游戏（第 1 关）', self.action_start, get_font(24)))
            b(Button((W // 2 - 130, 462, 260, 54), '选择关卡', self.action_select, get_font(24)))
            b(Button((W // 2 - 130, 532, 260, 54), '退出游戏', self.action_quit, get_font(24)))
        elif self.state == self.STATE_SELECT:
            cols = 3
            bw, bh, gap = 190, 82, 16
            x0 = (W - cols * bw - (cols - 1) * gap) // 2
            y0 = 150
            for i, lv in enumerate(LEVELS):
                r, c = divmod(i, cols)
                n = sum(1 for row in lv['grid'] for ch in row if ch in DIRECTIONS)
                b(LevelButton((x0 + c * (bw + gap), y0 + r * (bh + 14), bw, bh),
                              lv['name'], n, lambda i=i: self.action_level(i)))
            b(Button((W // 2 - 110, 566, 220, 48), '返回主菜单', self.action_start_menu, get_font(22)))
        elif self.state == self.STATE_GAME:
            b(Button((20, 24, 70, 46), '菜单', self.action_start_menu, get_font(20)))
            b(Button((W - 346, 24, 100, 46), '重新开始', self.action_restart, get_font(20)))
            b(Button((W - 236, 24, 80, 46), '提示', self.action_hint, get_font(20)))
            b(Button((W - 146, 24, 70, 46), '撤销', self.action_undo, get_font(20)))
        elif self.state == self.STATE_WIN:
            b(Button((W // 2 - 70, 356, 140, 50), '下一关', self.action_next, get_font(22)))
            b(Button((W // 2 - 70, 420, 140, 50), '重新开始', self.action_restart, get_font(22)))
            b(Button((W // 2 - 70, 484, 140, 46), '返回菜单', self.action_start_menu, get_font(20)))
        elif self.state == self.STATE_LOSE:
            b(Button((W // 2 - 70, 356, 140, 50), '重新开始', self.action_restart, get_font(22)))
            b(Button((W // 2 - 70, 420, 140, 50), '返回菜单', self.action_start_menu, get_font(22)))
        elif self.state == self.STATE_CLEAR:
            b(Button((W // 2 - 70, 356, 140, 50), '再玩一次', self.action_start, get_font(22)))
            b(Button((W // 2 - 70, 420, 140, 50), '返回菜单', self.action_start_menu, get_font(22)))

    # ---------- 事件与更新 ----------

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    btn.action()
                    return
            if self.state == self.STATE_GAME:
                cell = self.cell_at(*event.pos)
                if cell:
                    self.click_cell(*cell)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.state in (self.STATE_GAME, self.STATE_WIN,
                                  self.STATE_LOSE, self.STATE_CLEAR):
                    self.action_start_menu()
            elif self.state == self.STATE_GAME:
                if event.key == pygame.K_r:
                    self.action_restart()
                elif event.key == pygame.K_h:
                    self.action_hint()
                elif event.key == pygame.K_z:
                    self.action_undo()

    def update(self, dt):
        self.hint_timer = max(0.0, self.hint_timer - dt)
        self.animations = [a for a in self.animations if not a.update(dt)]
        self.floats = [f for f in self.floats if not f.update(dt)]
        if self.state == self.STATE_GAME and self.session:
            if self.session.tick(dt) and self._lose_timer is None:
                # 时间耗尽：延迟片刻显示失败界面，并给出“时间到！”提示
                self._lose_timer = 0.4
                self.floats.append(FloatText('时间到！', (W // 2, H // 2),
                                             color=BLOCKED_RED, cell=self.cell))
            if self._lose_timer is not None:
                self._lose_timer -= dt
                if self._lose_timer <= 0:
                    self._lose_timer = None
                    self.state = self.STATE_LOSE
                    self.build_buttons()
            elif (self.session.status == 'won'
                  and not any(isinstance(a, FlyOut) for a in self.animations)):
                # 最后一支箭头飞出动画结束后，切换到通关画面
                self.state = (self.STATE_CLEAR if self.level_index >= len(LEVELS) - 1
                              else self.STATE_WIN)
                self.build_buttons()

    # ---------- 绘制 ----------

    def draw(self):
        s = self.screen
        if self.state == self.STATE_START:
            self.draw_start(s)
        elif self.state == self.STATE_SELECT:
            self.draw_select(s)
        else:
            self.draw_game(s)
            if self.state != self.STATE_GAME:
                self.draw_overlay(s)
        for btn in self.buttons:
            btn.draw(s, self.mouse)

    def draw_start(self, s):
        s.fill(PAPER)
        title = get_font(66, bold=True).render('一箭又一箭', True, INK)
        s.blit(title, title.get_rect(center=(W // 2, 118)))
        sub = get_font(24).render('点击箭头，让它们按顺序飞出棋盘！', True, SUB_INK)
        s.blit(sub, sub.get_rect(center=(W // 2, 196)))
        lines = [
            '· 点击箭头：若其前方直到棋盘边界没有其他箭头，箭头飞出并消除；',
            '· 若被其他箭头阻挡，箭头保留，并消耗 1 次失误机会；',
            '· 每关有限时，清空本关全部箭头即通关；失误耗尽或超时则本关失败。',
        ]
        y = 264
        for line in lines:
            img = get_font(20).render(line, True, SUB_INK)
            s.blit(img, img.get_rect(center=(W // 2, y)))
            y += 34
        # 装饰：一排示例箭头
        x0 = W // 2 - 160
        for i, d in enumerate(['>', 'v', '<', '^']):
            draw_arrow(s, (x0 + i * 90, 336), d, 40, ARROW_BLUE, ARROW_DARK)

    def draw_select(self, s):
        s.fill(PAPER)
        title = get_font(40, bold=True).render('选择关卡', True, INK)
        s.blit(title, title.get_rect(center=(W // 2, 100)))
        tip = get_font(18).render('共 %d 关，全部可正常通关' % len(LEVELS), True, SUB_INK)
        s.blit(tip, tip.get_rect(center=(W // 2, 142)))

    def draw_hud(self, s):
        pygame.draw.rect(s, HUD_BG, (0, 0, W, HUD_H))
        pygame.draw.line(s, GRID_LINE, (0, HUD_H), (W, HUD_H), 3)
        lv = LEVELS[self.level_index]
        title = get_font(22, bold=True).render(
            '%s   (%d/%d)' % (lv['name'], self.level_index + 1, len(LEVELS)), True, INK)
        s.blit(title, (110, 30))
        # 旋转机制提示（仅在有旋转的关卡显示，放在标题行右侧）
        if self.session.rotate_every > 0:
            prog = self.session.rotate_progress()
            if prog is not None:
                rtxt = get_font(18, bold=True).render('🔄 再消 %d 个旋转' % prog, True, ARROW_GOLD)
                s.blit(rtxt, (400, 34))
        # 第二行：剩余箭头 | 失误次数 | 剩余时间（右侧）
        remain = self.session.board.count()
        txt = get_font(20).render('剩余箭头：%d' % remain, True, INK)
        s.blit(txt, (130, 78))
        lab = get_font(20).render('失误', True, INK)
        s.blit(lab, (330, 78))
        x = 392
        for i in range(self.session.max_mistakes):
            color = BLOCKED_RED if i < self.session.mistakes_left else (198, 188, 172)
            pygame.draw.circle(s, color, (x, 89), 11)
            x += 28
        if self.session.mistakes_left == 0:
            warn = get_font(20, bold=True).render('机会已用完！', True, BLOCKED_RED)
            s.blit(warn, (x + 14, 78))
        # 剩余时间：最后 30 秒变红提醒
        tl = self.session.time_limit
        if tl > 0:
            urgent = self.session.time_left <= 30
            color = BLOCKED_RED if urgent else INK
            ttxt = get_font(22, bold=True).render(
                '剩余时间 %s' % fmt_time(self.session.time_left), True, color)
            s.blit(ttxt, ttxt.get_rect(topright=(W - 24, 78)))
        else:
            ttxt = get_font(20).render('不限时', True, SUB_INK)
            s.blit(ttxt, ttxt.get_rect(topright=(W - 24, 80)))

    def draw_game(self, s):
        s.fill(PAPER)
        self.draw_hud(s)
        b = self.session.board
        bx, by = self.board_origin()
        rows, cols = b.rows, b.cols
        cell = self.cell
        pygame.draw.rect(s, (240, 235, 221),
                         (bx - 10, by - 10, cols * cell + 20, rows * cell + 20),
                         border_radius=12)
        # 悬停高亮
        hover = self.cell_at(*self.mouse)
        if hover:
            r, c = hover
            if b.arrow(r, c):
                pygame.draw.rect(s, (233, 227, 210),
                                 (bx + c * cell, by + r * cell, cell, cell))
        # 提示光圈
        if self.hint_target and self.hint_timer > 0:
            r, c = self.hint_target
            cx, cy = self.cell_center(r, c)
            radius = int(cell * 0.42 + 6 + 3 * math.sin(self.hint_timer * 10))
            pygame.draw.circle(s, HINT_YELLOW, (cx, cy), radius, 4)
        # 网格与箭头
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(bx + c * cell, by + r * cell, cell, cell)
                pygame.draw.rect(s, GRID_LINE, rect, width=1)
        for r in range(rows):
            for c in range(cols):
                ch = b.arrow(r, c)
                if ch is not None:
                    draw_arrow(s, self.cell_center(r, c), ch, cell * 0.55,
                               ARROW_BLUE, ARROW_DARK)
        for a in self.animations:
            a.draw(s)
        for f in self.floats:
            f.draw(s)

    def draw_overlay(self, s):
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill(OVERLAY)
        s.blit(ov, (0, 0))
        panel = pygame.Rect(W // 2 - 230, 172, 460, 396)
        pygame.draw.rect(s, (250, 246, 236), panel, border_radius=16)
        pygame.draw.rect(s, GRID_LINE, panel, width=2, border_radius=16)
        if self.state == self.STATE_WIN:
            title, sub = '恭喜通关！', '本关全部箭头已飞出'
        elif self.state == self.STATE_LOSE:
            reason = self.session.lose_reason if self.session else None
            if reason == 'time':
                title, sub = '时间耗尽', '本关限时已到，再试一次吧'
            else:
                title, sub = '本关失败', '失误次数已用完，再试一次吧'
        else:
            title, sub = '全部通关！', '你已经完成所有关卡'
        img = get_font(40, bold=True).render(title, True, INK)
        s.blit(img, img.get_rect(center=(W // 2, 260)))
        img2 = get_font(20).render(sub, True, SUB_INK)
        s.blit(img2, img2.get_rect(center=(W // 2, 310)))


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption('一箭又一箭 —— 点击式箭头解谜')
    app = App(screen)
    running = True
    while running:
        dt = app.clock.tick(FPS) / 1000.0
        app.mouse = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                app.handle_event(event)
        app.update(dt)
        app.draw()
        pygame.display.flip()
    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
