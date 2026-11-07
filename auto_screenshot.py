"""
自动截图脚本：无需手动操作，自动在关键时刻截图
"""
import sys
import os
import pygame
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.configs import *
from src.game.event_management import EventHandler
from src.game.state_management import GameState
from src.gui.screen_management import ScreenManager
from src.sounds import SoundManager

class AutoScreenshot:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Py-Pacman")
        
        self.game_state = GameState()
        self.events = EventHandler(self.screen, self.game_state)
        self.all_sprites = pygame.sprite.Group()
        self.gui = ScreenManager(self.screen, self.game_state, self.all_sprites)
        
        self.clock = pygame.time.Clock()
        self.screenshot_dir = "docs/screenshots"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
    def save_screenshot(self, name):
        """保存当前屏幕为 PNG"""
        filename = f"{self.screenshot_dir}/{name}.png"
        pygame.image.save(self.screen, filename)
        print(f"✓ 截图已保存: {filename}")
        return filename
        
    def run_auto_capture(self):
        """自动运行并截图"""
        # 加载最高分
        try:
            with open("levels/stats.json") as fp:
                stats = json.load(fp)
                self.game_state.highscore = stats['highscore']
                self.game_state.mins_played = stats['mins_played']
        except Exception as e:
            print(f"加载统计数据失败: {e}")
        
        # 创建幽灵模式事件
        CUSTOM_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(
            CUSTOM_EVENT,
            self.game_state.mode_change_events * 1000
        )
        self.game_state.custom_event = CUSTOM_EVENT
        
        # 初始化音效
        try:
            sound_manager = SoundManager()
            sound_manager.load_sound("dot", "assets/sounds/pacman_chomp.wav", channel=0)
            sound_manager.load_sound("death", "assets/sounds/pacman_death.wav", 0.7, 500, 1)
            sound_manager.load_sound("eat_ghost", "assets/sounds/pacman_eatghost.wav", 0.6, 100, 2)
            sound_manager.set_background_music("assets/sounds/backgroud.mp3")
            sound_manager.play_background_music()
        except:
            pass
        
        print("\n=== 自动截图模式 ===")
        print("游戏将自动运行 10 秒，期间会保存多张截图")
        print("按 Ctrl+C 提前退出\n")
        
        # 截图 1: 初始状态
        self._draw_frame()
        time.sleep(0.5)
        self.save_screenshot("01_游戏初始界面")
        
        # 模拟按键，让吃豆人移动
        self.game_state._GameState__direction = "r"  # 向右
        
        # 运行游戏并定期截图
        start_time = time.time()
        screenshot_times = [2, 4, 6, 8]  # 在第 2, 4, 6, 8 秒截图
        screenshot_idx = 0
        
        running = True
        while running and screenshot_idx < len(screenshot_times):
            elapsed = time.time() - start_time
            
            # 检查是否该截图了
            if screenshot_idx < len(screenshot_times) and elapsed >= screenshot_times[screenshot_idx]:
                self._draw_frame()
                self.save_screenshot(f"0{2+screenshot_idx}_游戏进行中_{elapsed:.0f}秒")
                screenshot_idx += 1
            
            # 处理事件（防止窗口卡死）
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.events.key_bindings(event.key)
                else:
                    self.events.handle_events(event)
            self.all_sprites.update(0.5)  # dt
            
            # 绘制
            self._draw_frame()
            self.clock.tick(60)
            
            # 10 秒后退出
            if elapsed > 10:
                running = False
        
        # 最后一张截图
        self._draw_frame()
        self.save_screenshot(f"0{2+screenshot_idx}_游戏结束画面")
        
        pygame.quit()
        print(f"\n✓ 自动截图完成！共保存 {screenshot_idx + 2} 张截图")
        print(f"📁 位置: {os.path.abspath(self.screenshot_dir)}/\n")
        
    def _draw_frame(self):
        """绘制一帧"""
        self.screen.fill((0, 0, 0))
        self.gui.draw_screens()
        self.all_sprites.draw(self.screen)
        pygame.display.flip()

if __name__ == '__main__':
    try:
        capture = AutoScreenshot()
        capture.run_auto_capture()
    except KeyboardInterrupt:
        print("\n\n用户中断，正在退出...")
        pygame.quit()
        sys.exit(0)
