"""
AI 玩家模块：让计算机自动玩吃豆人游戏。

本模块实现了一个基于规则的 AI，它会：
1. 寻找最近的豆子（BFS 寻路）
2. 躲避幽灵（危险检测）
3. 利用能量豆反击（策略决策）
4. 可视化决策过程（调试辅助）

设计理念：
- 优先保证生存（避开幽灵）
- 其次追求效率（最短路径吃豆）
- 最后考虑策略（能量豆反击）
"""

from collections import deque
from typing import Optional, Tuple, List
import random

from src.game.state_management import GameState
from src.utils.coord_utils import get_idx_from_coords


class PacmanAI:
    """
    吃豆人 AI 玩家：基于规则的决策系统。
    
    决策优先级：
    1. 生存：躲避附近的幽灵
    2. 反击：吃能量豆后追击幽灵
    3. 进食：寻找最近的豆子
    """
    
    def __init__(self, game_state: GameState, matrix: list, ghost_manager):
        """
        初始化 AI。
        
        Args:
            game_state: 游戏状态对象
            matrix: 迷宫矩阵（与 PacmanGrid 共享引用）
            ghost_manager: GhostManager 实例，用于访问 ghosts_list
        """
        self.game_state = game_state
        self.matrix = matrix
        self.ghost_manager = ghost_manager
        self.num_rows = len(matrix)
        self.num_cols = len(matrix[0]) if matrix else 0
        
        # 调试信息
        self.debug_info = {
            'current_target': None,  # 当前目标格子
            'path': [],  # 规划的路径
            'decision': 'idle',  # 当前决策：flee/chase/eat/idle
            'danger_level': 0,  # 危险等级 0-10
            'nearest_dot': None,  # 最近的豆子
        }
    
    def decide_direction(self, pacman_pos: Tuple[int, int], 
                        pacman_direction: str) -> str:
        """
        决策：应该往哪个方向移动。
        
        Args:
            pacman_pos: 吃豆人当前位置 (pixel_x, pixel_y)
            pacman_direction: 当前方向 'l'/'r'/'u'/'d'
        
        Returns:
            建议的方向 'l'/'r'/'u'/'d'
        """
        # 将像素坐标转换为网格坐标
        grid_pos = self._pixel_to_grid(pacman_pos)
        
        # 1. 检查危险：附近是否有幽灵
        danger_level, nearest_ghost = self._assess_danger(grid_pos)
        self.debug_info['danger_level'] = danger_level
        
        # 2. 如果很危险，优先逃跑
        if danger_level > 6:
            self.debug_info['decision'] = 'flee'
            return self._flee_from_ghosts(grid_pos, nearest_ghost)
        
        # 3. 如果吃了能量豆且幽灵在恐慌状态，可以追击
        if self.game_state.is_pacman_powered and nearest_ghost:
            self.debug_info['decision'] = 'chase'
            return self._chase_ghost(grid_pos, nearest_ghost)
        
        # 4. 否则，找最近的豆子
        self.debug_info['decision'] = 'eat'
        return self._seek_nearest_dot(grid_pos, pacman_direction)
    
    def _pixel_to_grid(self, pixel_pos: Tuple[int, int]) -> Tuple[int, int]:
        """像素坐标转网格坐标"""
        from src.configs import CELL_SIZE, SCREEN_WIDTH, SCREEN_HEIGHT
        
        # 计算迷宫起始偏移（与 PacmanGrid 一致）
        start_x = (SCREEN_WIDTH - CELL_SIZE[0] * self.num_cols) // 2
        start_y = (SCREEN_HEIGHT - CELL_SIZE[0] * self.num_rows) // 2
        
        # 转换为网格坐标
        col = int((pixel_pos[0] - start_x) / CELL_SIZE[0])
        row = int((pixel_pos[1] - start_y) / CELL_SIZE[0])
        
        # 限制在有效范围内
        row = max(0, min(row, self.num_rows - 1))
        col = max(0, min(col, self.num_cols - 1))
        
        return (row, col)
    
    def _assess_danger(self, grid_pos: Tuple[int, int]) -> Tuple[int, Optional[Tuple[int, int]]]:
        """
        评估危险等级。
        
        Returns:
            (danger_level, nearest_ghost_pos)
            danger_level: 0-10，越高越危险
            nearest_ghost_pos: 最近幽灵的网格坐标
        """
        min_dist = float('inf')
        nearest_ghost = None
        danger_level = 0
        
        # 遍历所有幽灵
        for ghost in self.ghost_manager.ghosts_list:
            ghost_grid = self._pixel_to_grid((ghost.rect.x, ghost.rect.y))
            dist = self._manhattan_distance(grid_pos, ghost_grid)
            
            # 如果幽灵不在恐慌状态，才算危险
            if not ghost.is_scared:
                if dist < min_dist:
                    min_dist = dist
                    nearest_ghost = ghost_grid
                
                # 距离越近，危险等级越高
                if dist < 2:
                    danger_level = max(danger_level, 10)
                elif dist < 4:
                    danger_level = max(danger_level, 7)
                elif dist < 6:
                    danger_level = max(danger_level, 4)
                elif dist < 8:
                    danger_level = max(danger_level, 2)
        
        return danger_level, nearest_ghost
    
    def _flee_from_ghosts(self, grid_pos: Tuple[int, int], 
                         ghost_pos: Optional[Tuple[int, int]]) -> str:
        """
        逃跑策略：远离幽灵。
        
        使用"排斥力"算法：计算所有幽灵的反方向向量，选择合力最大的方向。
        """
        if not ghost_pos:
            return self._seek_nearest_dot(grid_pos, 'r')
        
        # 计算逃跑方向（远离幽灵）
        dr = grid_pos[0] - ghost_pos[0]
        dc = grid_pos[1] - ghost_pos[1]
        
        # 选择主要逃跑方向
        if abs(dr) > abs(dc):
            return 'd' if dr > 0 else 'u'
        else:
            return 'r' if dc > 0 else 'l'
    
    def _chase_ghost(self, grid_pos: Tuple[int, int], 
                    ghost_pos: Tuple[int, int]) -> str:
        """
        追击策略：幽灵恐慌时追击。
        
        使用 BFS 找到通往幽灵的最短路径。
        """
        path = self._bfs(grid_pos, ghost_pos, avoid_ghosts=False)
        
        if path and len(path) > 1:
            next_pos = path[1]
            return self._grid_to_direction(grid_pos, next_pos)
        
        # 找不到路径时，随机移动
        return random.choice(['l', 'r', 'u', 'd'])
    
    def _seek_nearest_dot(self, grid_pos: Tuple[int, int], 
                         current_direction: str) -> str:
        """
        进食策略：寻找最近的豆子。
        
        使用 BFS 搜索所有可达的豆子，选择最近的。
        """
        # 找到所有豆子
        dots = self._find_all_dots()
        
        if not dots:
            # 没有豆子了，随机移动
            return random.choice(['l', 'r', 'u', 'd'])
        
        # 找最近的豆子
        nearest_dot = None
        min_dist = float('inf')
        best_path = []
        
        for dot in dots:
            path = self._bfs(grid_pos, dot, avoid_ghosts=True)
            if path and len(path) < min_dist:
                min_dist = len(path)
                nearest_dot = dot
                best_path = path
        
        # 更新调试信息
        self.debug_info['nearest_dot'] = nearest_dot
        self.debug_info['path'] = best_path
        
        if best_path and len(best_path) > 1:
            next_pos = best_path[1]
            self.debug_info['current_target'] = nearest_dot
            return self._grid_to_direction(grid_pos, next_pos)
        
        # 找不到路径时，保持当前方向
        return current_direction
    
    def _find_all_dots(self) -> List[Tuple[int, int]]:
        """找到所有剩余的豆子"""
        dots = []
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if self.matrix[r][c] in ['dot', 'power']:
                    dots.append((r, c))
        return dots
    
    def _bfs(self, start: Tuple[int, int], goal: Tuple[int, int], 
            avoid_ghosts: bool = True) -> Optional[List[Tuple[int, int]]]:
        """
        BFS 寻路算法。
        
        Args:
            start: 起始位置 (row, col)
            goal: 目标位置 (row, col)
            avoid_ghosts: 是否避开幽灵
        
        Returns:
            路径列表 [(row, col), ...] 或 None
        """
        queue = deque([(start, [start])])
        visited = {start}
        
        # 获取幽灵位置（用于避开）
        ghost_positions = set()
        if avoid_ghosts:
            for ghost in self.ghost_manager.ghosts_list:
                if not ghost.is_scared:
                    ghost_grid = self._pixel_to_grid((ghost.rect.x, ghost.rect.y))
                    ghost_positions.add(ghost_grid)
        
        while queue:
            (curr, path) = queue.popleft()
            
            # 到达目标
            if curr == goal:
                return path
            
            # 四个方向扩展
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                next_pos = (curr[0] + dr, curr[1] + dc)
                
                # 检查边界和可通行性
                if (self._is_valid_position(next_pos) and 
                    next_pos not in visited and
                    next_pos not in ghost_positions):
                    visited.add(next_pos)
                    queue.append((next_pos, path + [next_pos]))
        
        return None
    
    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """检查位置是否有效（在边界内且可通行）"""
        row, col = pos
        
        # 边界检查
        if row < 0 or row >= self.num_rows or col < 0 or col >= self.num_cols:
            return False
        
        # 可通行检查
        cell = self.matrix[row][col]
        return cell in ['void', 'dot', 'power']
    
    def _grid_to_direction(self, from_pos: Tuple[int, int], 
                          to_pos: Tuple[int, int]) -> str:
        """网格坐标差转方向"""
        dr = to_pos[0] - from_pos[0]
        dc = to_pos[1] - from_pos[1]
        
        if dr == -1:
            return 'u'
        elif dr == 1:
            return 'd'
        elif dc == -1:
            return 'l'
        elif dc == 1:
            return 'r'
        else:
            return 'r'  # 默认
    
    def _manhattan_distance(self, pos1: Tuple[int, int], 
                           pos2: Tuple[int, int]) -> int:
        """曼哈顿距离"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def get_debug_info(self) -> dict:
        """获取调试信息（用于可视化）"""
        return self.debug_info.copy()
