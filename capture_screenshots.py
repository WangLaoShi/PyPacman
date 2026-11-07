"""
自动截图脚本：启动游戏并在关键时刻保存截图。
用于教程网站素材。
"""
import sys
import os
import pygame
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.configs import *
from src.game.event_management import EventHandler
from src.game.state_management import GameState
from src.gui.screen_management import ScreenManager
from src.sounds import SoundManager

class ScreenshotCapture:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Py-Pacman - 截图模式")
        
        self.game_state = GameState()
        self.events = EventHandler(self.screen, self.game_state)
        self.all_sprites = pygame.sprite.Group()
        self.gui = ScreenManager(self.screen, self.game_state, self.all_sprites)
        
        self.clock = pygame.time.Clock()
        self.screenshot_dir = "docs/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def save_screenshot(self, name):
        """保存当前屏幕为 PNG"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.screenshot_dir}/{name}_{timestamp}.png"
        pygame.image.save(self.screen, filename)
        print(f"截图已保存: {filename}")
        
    def run_capture_session(self):
        """运行截图捕获会话"""
        # 加载最高分
        try:
            with open("levels/stats.json") as fp:
                stats = json.load(fp)
                self.game_state.highscore = stats['highscore']
                self.game_state.mins_played = stats['mins_played']
        except:
            pass
        
        # 创建幽灵模式事件
        CUSTOM_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(
            CUSTOM_EVENT,
            self.game_state.mode_change_events * 1000
        )
        self.game_state.custom_event = CUSTOM_EVENT
        
        # 初始化音效（可选）
        try:
            sound_manager = SoundManager()
            sound_manager.load_sound("dot", "assets/sounds/pacman_chomp.wav", channel=0)
            sound_manager.load_sound("death", "assets/sounds/pacman_death.wav", 0.7, 500, 1)
            sound_manager.load_sound("eat_ghost", "assets/sounds/pacman_eatghost.wav", 0.6, 100, 2)
            sound_manager.set_background_music("assets/sounds/backgroud.mp3")
            sound_manager.play_background_music()
        except:
            print("音效加载失败，继续无音效模式")
        
        print("\n=== 截图捕获模式 ===")
        print("按 S 键保存当前屏幕截图")
        print("按 Q 键或关闭窗口退出")
        print("===================\n")
        
        running = True
        frame_count = 0
        
        while running:
            dt = self.clock.tick(60)
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_s:
                        # 保存截图
                        self.save_screenshot(f"screenshot_{frame_count}")
            
            # 更新游戏状态
            self.events.key_bindings()
            
            # 绘制
            self.screen.fill((0, 0, 0))
            self.gui.draw_screens()
            self.all_sprites.update(dt / 100.0)
            self.all_sprites.draw(self.screen)
            
            # 更新显示
            pygame.display.flip()
            frame_count += 1
        
        pygame.quit()
        print(f"\n共保存 {len(os.listdir(self.screenshot_dir))} 张截图到 {self.screenshot_dir}/")

if __name__ == '__main__':
    capture = ScreenshotCapture()
    capture.run_capture_session()
