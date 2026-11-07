"""
AI 玩家入口：用 AI 替代人类键盘输入，自动控制吃豆人。

本文件结构类似 ``src/runner.py`` 的 ``GameRun``，但主循环里：
1. 不调用 ``EventHandler.handle_events`` 控制方向（只保留 Q 键退出）
2. 每帧调用 ``PacmanAI.decide_direction()`` 获取 AI 决策方向
3. 将 AI 方向写入 ``game_state.direction``（Pacman 的 ``movement_bind`` 会读取）
4. 绘制阶段调用 ``AIVisualizer.draw()`` 叠加调试信息

运行方式：
    cd PyPacman
    source .venv/bin/activate
    python ai_main.py

按 Q 键或关闭窗口退出游戏。
"""

import sys

import pygame

from src.configs import *
from src.game.state_management import GameState
from src.gui.screen_management import ScreenManager
from src.sounds import SoundManager
from src.ai import PacmanAI, AIVisualizer
from src.log_handle import get_logger

logger = get_logger(__name__)


class AIGameRun:
    """AI 玩家版本的游戏主控。"""

    def __init__(self):
        logger.info("初始化 pygame（AI 模式）")
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Py-Pacman AI Mode")
        logger.info("pygame 初始化完成")

        # GameState 是单一数据源：分数、方向、幽灵模式等。
        self.game_state = GameState()
        logger.info("游戏状态对象已创建")

        # ScreenManager 负责创建 PacmanGrid 并管理精灵组。
        self.all_sprites = pygame.sprite.Group()
        self.gui = ScreenManager(self.screen, self.game_state, self.all_sprites)
        logger.info("屏幕管理器已创建")

        # AI 玩家：传入 game_state、matrix 和 ghost_manager 引用。
        # matrix 来自 PacmanGrid（gui.pacman 是 PacmanGrid 实例）。
        # ghost_manager 来自 PacmanGrid.ghost（GhostManager 实例）。
        self.ai = PacmanAI(
            self.game_state,
            self.gui.pacman._matrix,  # PacmanGrid 的迷宫矩阵引用
            self.gui.pacman.ghost  # GhostManager 引用，用于访问 ghosts_list
        )
        logger.info("AI 玩家已创建")

        # 可视化调试器：在屏幕上绘制 AI 决策过程。
        self.visualizer = AIVisualizer(self.screen)
        logger.info("AI 可视化调试器已创建")

    def initialize_highscore(self):
        """读取历史最高分。"""
        import json
        try:
            with open("levels/stats.json") as fp:
                stats = json.load(fp)
                self.game_state.highscore = stats['highscore']
                self.game_state.mins_played = stats.get('mins_played', 0)
        except FileNotFoundError:
            logger.warning("stats.json 不存在，使用默认最高分 0")
            self.game_state.highscore = 0

    def create_ghost_mode_event(self):
        """创建幽灵模式切换的定时事件。"""
        CUSTOM_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(
            CUSTOM_EVENT,
            self.game_state.mode_change_events * 1000
        )
        self.game_state.custom_event = CUSTOM_EVENT

    def initialize_sounds(self):
        """加载音效。"""
        sound_manager = SoundManager()
        sound_manager.load_sound("dot", "assets/sounds/pacman_chomp.wav", channel=0)
        sound_manager.load_sound("death", "assets/sounds/pacman_death.wav", 0.7, 500, 1)
        sound_manager.load_sound("eat_ghost", "assets/sounds/pacman_eatghost.wav", 0.6, 100, 2)
        sound_manager.set_background_music("assets/sounds/backgroud.mp3")
        sound_manager.play_background_music()

    def check_highscores(self):
        """每帧检查是否刷新最高分。"""
        if self.game_state.points > self.game_state.highscore:
            self.game_state.highscore = self.game_state.points

    def update_highscore(self):
        """游戏结束时写入最高分到文件。"""
        import json
        with open("levels/stats.json", 'w') as fp:
            json.dump(
                {"highscore": self.game_state.highscore,
                 "mins_played": self.game_state.mins_played},
                fp,
                indent=4
            )

    def handle_events(self):
        """
        处理 pygame 事件队列。

        AI 模式下只响应：
        - QUIT：关闭窗口
        - Q 键：主动退出

        不再处理方向键，因为方向由 AI 决策。
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_state.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    self.game_state.running = False
                # 可以扩展其他调试快捷键，如：
                # elif event.key == pygame.K_d:  # 切换调试模式
                #     self.ai.toggle_debug()

    def update_ai(self):
        """
        更新 AI 决策并写入 game_state.direction。

        这是与人类玩家版本的核心区别：
        - 人类版本：EventHandler 读键盘 → 写 game_state.direction
        - AI 版本：PacmanAI.decide_direction() → 写 game_state.direction

        AI 需要：
        - pacman 当前位置（像素坐标，来自 Sprite.rect）
        - pacman 当前方向（来自 game_state.pacman_direction）
        """
        # 获取 Pacman 精灵的 rect（碰撞矩形，包含位置信息）。
        # gui.pacman 是 PacmanGrid，其 .pacman 是 Pacman Sprite。
        pacman_sprite = self.gui.pacman.pacman
        pacman_pos = (pacman_sprite.rect.x, pacman_sprite.rect.y)

        # 获取 Pacman 当前移动方向（由 movement_bind 写入）。
        pacman_direction = self.game_state.pacman_direction

        # AI 决策：返回 'l'/'r'/'u'/'d' 或 ''（保持当前方向）。
        ai_direction = self.ai.decide_direction(pacman_pos, pacman_direction)

        # 将 AI 决策写入 game_state，Pacman 的 movement_bind 会读取。
        if ai_direction:  # 非空字符串才更新
            self.game_state.direction = ai_direction

    def draw_debug_info(self):
        """
        绘制 AI 调试信息。

        在精灵绘制之后调用，叠加显示：
        - 目标位置（绿色圆圈）
        - 路径（蓝色线条）
        - 危险区域（红色半透明）
        - 决策状态（文字）
        """
        pacman_sprite = self.gui.pacman.pacman
        pacman_pos = (pacman_sprite.rect.x, pacman_sprite.rect.y)

        # 获取 AI 的调试信息字典。
        debug_info = self.ai.get_debug_info()

        # 可视化调试器绘制。
        self.visualizer.draw(debug_info, pacman_pos)

    def main(self):
        """
        AI 版本的主循环。

        流程：
        1. handle_events() - 只处理退出事件
        2. update_ai() - AI 决策方向
        3. fill 清屏
        4. draw_screens() - 画迷宫和 HUD
        5. all_sprites.draw() - 画精灵
        6. draw_debug_info() - 画 AI 调试信息
        7. all_sprites.update(dt) - 更新精灵位置
        8. check_highscores() - 检查最高分
        9. flip 刷新显示
        10. tick 限帧
        """
        clock = pygame.time.Clock()
        dt = None

        # 初始化各子系统。
        self.create_ghost_mode_event()
        self.initialize_sounds()
        self.initialize_highscore()

        logger.info("AI 玩家主循环开始")

        while self.game_state.running:
            self.game_state.current_time = pygame.time.get_ticks()

            # 1. 事件处理（只有退出，没有方向键）。
            self.handle_events()

            # 2. AI 决策（替代人类键盘输入）。
            self.update_ai()

            # 3. 清屏。
            self.screen.fill(Colors.BLACK)

            # 4-5. 绘制迷宫、HUD、精灵。
            self.gui.draw_screens()
            self.all_sprites.draw(self.screen)

            # 6. 绘制 AI 调试信息（叠加在精灵之上）。
            self.draw_debug_info()

            # 7. 更新精灵位置（Pacman 移动、幽灵 AI）。
            self.all_sprites.update(dt)

            # 8. 检查最高分。
            self.check_highscores()

            # 9. 刷新显示。
            pygame.display.flip()

            # 10. 限帧并计算 dt。
            dt = clock.tick(self.game_state.fps)
            dt /= 100

        # 循环结束，写入最高分并退出。
        self.update_highscore()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PyPacman AI 模式启动")
    logger.info("按 Q 键退出游戏")
    logger.info("=" * 60)

    game = AIGameRun()
    game.main()
