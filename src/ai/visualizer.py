"""
AI 可视化调试模块：在屏幕上绘制 AI 的决策过程。

可视化元素：
- 绿色圆圈：AI 的目标豆子
- 蓝色线条：AI 规划的路径
- 红色区域：危险范围（幽灵附近）
- 文字信息：当前决策状态
"""

import pygame
from pygame.surface import Surface
from typing import Tuple, List, Optional

from src.configs import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT, Colors


class AIVisualizer:
    """AI 决策可视化器"""
    
    def __init__(self, screen: Surface):
        """
        初始化可视化器。
        
        Args:
            screen: pygame 主屏幕
        """
        self.screen = screen
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # 计算迷宫起始位置（与 PacmanGrid 一致）
        self.start_x = (SCREEN_WIDTH - CELL_SIZE[0] * 35) // 2
        self.start_y = (SCREEN_HEIGHT - CELL_SIZE[0] * 32) // 2
    
    def draw(self, debug_info: dict, pacman_pos: Tuple[int, int]):
        """
        绘制所有调试信息。
        
        Args:
            debug_info: AI 的调试信息字典
            pacman_pos: 吃豆人当前位置 (pixel_x, pixel_y)
        """
        # 绘制路径
        if debug_info.get('path'):
            self._draw_path(debug_info['path'])
        
        # 绘制目标
        if debug_info.get('current_target'):
            self._draw_target(debug_info['current_target'])
        
        # 绘制危险区域
        if debug_info.get('danger_level', 0) > 3:
            self._draw_danger_zone(pacman_pos, debug_info['danger_level'])
        
        # 绘制决策信息
        self._draw_decision_info(debug_info, pacman_pos)
    
    def _grid_to_pixel(self, grid_pos: Tuple[int, int]) -> Tuple[int, int]:
        """网格坐标转像素坐标（格子中心）"""
        row, col = grid_pos
        pixel_x = self.start_x + col * CELL_SIZE[0] + CELL_SIZE[0] // 2
        pixel_y = self.start_y + row * CELL_SIZE[0] + CELL_SIZE[0] // 2
        return (pixel_x, pixel_y)
    
    def _draw_path(self, path: List[Tuple[int, int]]):
        """绘制 AI 规划的路径"""
        if len(path) < 2:
            return
        
        # 将路径点转换为像素坐标
        points = [self._grid_to_pixel(pos) for pos in path]
        
        # 绘制蓝色线条
        pygame.draw.lines(self.screen, (100, 150, 255), False, points, 2)
        
        # 绘制路径点（小圆点）
        for point in points[1:]:  # 跳过起点
            pygame.draw.circle(self.screen, (100, 150, 255), point, 3)
    
    def _draw_target(self, target: Tuple[int, int]):
        """绘制目标位置"""
        pixel_pos = self._grid_to_pixel(target)
        
        # 绘制绿色圆圈（脉动效果）
        radius = 8 + int(2 * pygame.time.get_ticks() / 200 % 2)
        pygame.draw.circle(self.screen, (100, 255, 100), pixel_pos, radius, 2)
        
        # 绘制中心点
        pygame.draw.circle(self.screen, (100, 255, 100), pixel_pos, 3)
    
    def _draw_danger_zone(self, pacman_pos: Tuple[int, int], danger_level: int):
        """绘制危险区域"""
        # 根据危险等级调整透明度和大小
        alpha = min(255, danger_level * 25)
        radius = 30 + danger_level * 5
        
        # 创建透明表面
        danger_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        
        # 绘制红色渐变圆圈
        color = (255, 50, 50, alpha // 2)
        pygame.draw.circle(danger_surface, color, (radius, radius), radius)
        
        # 绘制到屏幕
        self.screen.blit(danger_surface, 
                        (pacman_pos[0] - radius, pacman_pos[1] - radius))
    
    def _draw_decision_info(self, debug_info: dict, pacman_pos: Tuple[int, int]):
        """绘制决策信息文字"""
        # 决策状态
        decision = debug_info.get('decision', 'idle')
        decision_colors = {
            'flee': (255, 100, 100),  # 红色
            'chase': (255, 200, 100),  # 橙色
            'eat': (100, 255, 100),   # 绿色
            'idle': (200, 200, 200),  # 灰色
        }
        color = decision_colors.get(decision, (200, 200, 200))
        
        # 决策文字
        decision_text = self.font.render(f"AI: {decision.upper()}", True, color)
        self.screen.blit(decision_text, (10, 10))
        
        # 危险等级
        danger_level = debug_info.get('danger_level', 0)
        danger_text = self.small_font.render(
            f"Danger: {danger_level}/10", 
            True, 
            (255, 100, 100) if danger_level > 5 else (200, 200, 200)
        )
        self.screen.blit(danger_text, (10, 35))
        
        # 目标信息
        if debug_info.get('nearest_dot'):
            target = debug_info['nearest_dot']
            target_text = self.small_font.render(
                f"Target: ({target[0]}, {target[1]})", 
                True, 
                (100, 255, 100)
            )
            self.screen.blit(target_text, (10, 55))
        
        # 路径长度
        path_length = len(debug_info.get('path', []))
        path_text = self.small_font.render(
            f"Path: {path_length} steps", 
            True, 
            (100, 150, 255)
        )
        self.screen.blit(path_text, (10, 75))
        
        # 位置信息
        pos_text = self.small_font.render(
            f"Pos: ({pacman_pos[0]}, {pacman_pos[1]})", 
            True, 
            (200, 200, 200)
        )
        self.screen.blit(pos_text, (10, 95))
