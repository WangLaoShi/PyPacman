"""
AI 玩家测试脚本：运行游戏并记录 AI 的表现。

运行方式：
    cd PyPacman
    source .venv/bin/activate
    python test_ai.py

功能：
1. 自动运行游戏（无需人工干预）
2. 每 5 秒记录一次 AI 状态（决策、分数、危险等级）
3. 游戏结束时输出统计信息
4. 按 Q 键可随时退出
"""

import sys
import time
import pygame

from src.configs import *
from src.game.state_management import GameState
from src.gui.screen_management import ScreenManager
from src.sounds import SoundManager
from src.ai import PacmanAI, AIVisualizer
from src.log_handle import get_logger

logger = get_logger(__name__)


class AITest:
    """AI 测试运行器。"""
    
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Py-Pacman AI Test")
        
        self.game_state = GameState()
        self.all_sprites = pygame.sprite.Group()
        self.gui = ScreenManager(self.screen, self.game_state, self.all_sprites)
        
        self.ai = PacmanAI(
            self.game_state,
            self.gui.pacman._matrix,
            self.gui.pacman.ghost
        )
        
        self.visualizer = AIVisualizer(self.screen)
        
        # 统计信息
        self.start_time = None
        self.last_log_time = 0
        self.decision_counts = {
            'flee': 0,
            'chase': 0,
            'eat': 0,
            'idle': 0
        }
        self.frame_count = 0
        
    def initialize_highscore(self):
        import json
        try:
            with open("levels/stats.json") as fp:
                stats = json.load(fp)
                self.game_state.highscore = stats['highscore']
        except FileNotFoundError:
            self.game_state.highscore = 0
    
    def create_ghost_mode_event(self):
        CUSTOM_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(
            CUSTOM_EVENT,
            self.game_state.mode_change_events * 1000
        )
        self.game_state.custom_event = CUSTOM_EVENT
    
    def initialize_sounds(self):
        sound_manager = SoundManager()
        sound_manager.load_sound("dot", "assets/sounds/pacman_chomp.wav", channel=0)
        sound_manager.load_sound("death", "assets/sounds/pacman_death.wav", 0.7, 500, 1)
        sound_manager.load_sound("eat_ghost", "assets/sounds/pacman_eatghost.wav", 0.6, 100, 2)
        sound_manager.set_background_music("assets/sounds/backgroud.mp3")
        sound_manager.play_background_music()
    
    def log_ai_state(self, elapsed_time):
        """每 5 秒记录一次 AI 状态。"""
        if elapsed_time - self.last_log_time >= 5:
            debug_info = self.ai.get_debug_info()
            pacman_sprite = self.gui.pacman.pacman
            
            logger.info("=" * 60)
            logger.info(f"时间: {elapsed_time:.1f}s | 帧数: {self.frame_count}")
            logger.info(f"分数: {self.game_state.points} | 最高分: {self.game_state.highscore}")
            logger.info(f"关卡: {self.game_state.level}")
            logger.info(f"Pacman 位置: ({pacman_sprite.rect.x}, {pacman_sprite.rect.y})")
            logger.info(f"当前决策: {debug_info['decision']}")
            logger.info(f"危险等级: {debug_info['danger_level']}/10")
            logger.info(f"目标位置: {debug_info.get('current_target', 'None')}")
            logger.info(f"路径长度: {len(debug_info.get('path', []))}")
            logger.info(f"决策统计: {self.decision_counts}")
            logger.info("=" * 60)
            
            self.last_log_time = elapsed_time
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
        return True
    
    def update_ai(self):
        """更新 AI 决策并记录统计。"""
        pacman_sprite = self.gui.pacman.pacman
        pacman_pos = (pacman_sprite.rect.x, pacman_sprite.rect.y)
        pacman_direction = self.game_state.pacman_direction
        
        # AI 决策
        ai_direction = self.ai.decide_direction(pacman_pos, pacman_direction)
        
        # 记录决策
        debug_info = self.ai.get_debug_info()
        decision = debug_info['decision']
        if decision in self.decision_counts:
            self.decision_counts[decision] += 1
        
        # 应用方向
        if ai_direction:
            self.game_state.direction = ai_direction
    
    def print_final_stats(self):
        """输出最终统计。"""
        elapsed = time.time() - self.start_time
        logger.info("\n" + "=" * 60)
        logger.info("游戏结束 - 最终统计")
        logger.info("=" * 60)
        logger.info(f"游戏时长: {elapsed:.1f} 秒")
        logger.info(f"总帧数: {self.frame_count}")
        logger.info(f"平均 FPS: {self.frame_count / elapsed:.2f}")
        logger.info(f"最终分数: {self.game_state.points}")
        logger.info(f"最高分: {self.game_state.highscore}")
        logger.info(f"通过关卡: {self.game_state.level - 1}")
        logger.info(f"\n决策分布:")
        for decision, count in self.decision_counts.items():
            pct = count / max(1, sum(self.decision_counts.values())) * 100
            logger.info(f"  {decision:8s}: {count:5d} ({pct:5.1f}%)")
        logger.info("=" * 60 + "\n")
    
    def run(self):
        """主测试循环。"""
        clock = pygame.time.Clock()
        dt = None
        
        self.create_ghost_mode_event()
        self.initialize_sounds()
        self.initialize_highscore()
        
        self.start_time = time.time()
        logger.info("AI 测试开始")
        
        running = True
        while running and self.game_state.running:
            self.game_state.current_time = pygame.time.get_ticks()
            
            # 事件处理
            running = self.handle_events()
            
            # AI 决策
            self.update_ai()
            
            # 绘制
            self.screen.fill(Colors.BLACK)
            self.gui.draw_screens()
            self.all_sprites.draw(self.screen)
            
            # 调试可视化
            pacman_sprite = self.gui.pacman.pacman
            pacman_pos = (pacman_sprite.rect.x, pacman_sprite.rect.y)
            self.visualizer.draw(self.ai.get_debug_info(), pacman_pos)
            
            # 更新
            self.all_sprites.update(dt)
            
            pygame.display.flip()
            dt = clock.tick(self.game_state.fps)
            dt /= 100
            
            self.frame_count += 1
            
            # 定期记录
            elapsed = time.time() - self.start_time
            self.log_ai_state(elapsed)
        
        self.print_final_stats()
        
        # 保存最高分
        import json
        with open("levels/stats.json", 'w') as fp:
            json.dump(
                {"highscore": self.game_state.highscore,
                 "mins_played": self.game_state.mins_played},
                fp,
                indent=4
            )
        
        pygame.quit()


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("PyPacman AI 测试模式")
    logger.info("按 Q 键退出测试")
    logger.info("每 5 秒输出一次 AI 状态")
    logger.info("=" * 60)
    
    test = AITest()
    test.run()
