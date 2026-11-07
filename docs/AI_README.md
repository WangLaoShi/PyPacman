# PyPacman AI 玩家模块

## 概述

本项目为 PyPacman 游戏实现了一个基于规则的 AI 玩家，能够自动控制吃豆人在迷宫中导航、躲避幽灵并收集豆子。

## 核心组件

### 1. PacmanAI (`src/ai/pacman_ai.py`)

基于规则的决策系统，采用优先级架构：

**决策优先级：**
1. **生存（Flee）**：当危险等级 > 6 时，优先躲避附近的幽灵
2. **反击（Chase）**：当能量豆生效且幽灵恐慌时，追击幽灵
3. **进食（Eat）**：使用 BFS 寻路算法寻找最近的豆子

**关键方法：**
- `decide_direction(pacman_pos, pacman_direction)` - 主决策函数
- `_assess_danger(grid_pos)` - 评估危险等级（0-10）
- `_bfs(start, goal, avoid_ghosts)` - BFS 寻路算法
- `_flee_from_ghosts(grid_pos, nearest_ghost)` - 逃跑策略
- `_chase_ghost(grid_pos, nearest_ghost)` - 追击策略
- `_seek_nearest_dot(grid_pos, pacman_direction)` - 吃豆策略

**危险等级计算：**
- 距离 0-2 格：危险等级 10（极危险）
- 距离 3-5 格：危险等级 7-9
- 距离 6-10 格：危险等级 4-6
- 距离 >10 格：危险等级 0-3

### 2. AIVisualizer (`src/ai/visualizer.py`)

可视化调试工具，实时显示 AI 的决策过程：

**绘制内容：**
- **绿色圆圈** - AI 当前目标位置
- **蓝色线条** - 规划的路径
- **红色半透明区域** - 危险区域（幽灵附近）
- **文字信息** - 决策状态、危险等级、目标、路径长度

### 3. 集成入口

**ai_main.py** - AI 模式游戏入口
```bash
cd PyPacman
source .venv/bin/activate
python ai_main.py
```

**test_ai.py** - AI 测试脚本（带统计日志）
```bash
cd PyPacman
source .venv/bin/activate
python test_ai.py
```

## 使用方法

### 运行 AI 玩家

```bash
# 激活虚拟环境
cd PyPacman
source .venv/bin/activate

# 运行 AI 模式
python ai_main.py

# 按 Q 键退出
```

### 测试 AI 性能

```bash
# 运行测试脚本（每 5 秒输出统计）
python test_ai.py

# 按 Q 键随时结束测试
```

测试输出示例：
```
============================================================
时间: 15.1s | 帧数: 539
分数: 180 | 最高分: 4590
关卡: 1
Pacman 位置: (306, 400)
当前决策: eat
危险等级: 0/10
目标位置: (16, 7)
路径长度: 2
决策统计: {'flee': 453, 'chase': 0, 'eat': 86, 'idle': 0}
============================================================
```

## 技术实现

### 架构设计

```
ai_main.py (入口)
    ↓
AIGameRun (游戏循环)
    ↓
    ├── PacmanAI (决策引擎)
    │   ├── _assess_danger() - 危险评估
    │   ├── _bfs() - 路径规划
    │   └── decide_direction() - 主决策
    │
    ├── AIVisualizer (可视化)
    │   └── draw() - 绘制调试信息
    │
    └── GameState (状态管理)
        ├── direction - AI 写入的方向
        ├── is_pacman_powered - 能量状态
        └── ghosts_list - 幽灵位置
```

### 数据流

1. **输入**：
   - Pacman 位置（像素坐标）
   - Pacman 当前方向
   - 幽灵位置列表
   - 迷宫矩阵（可吃豆状态）

2. **处理**：
   - 像素坐标 → 网格坐标
   - 危险评估（曼哈顿距离）
   - BFS 寻路（避免幽灵）
   - 决策优先级判断

3. **输出**：
   - 方向指令（'l'/'r'/'u'/'d'）
   - 调试信息（目标、路径、危险等级）

### 关键算法

**BFS 寻路：**
```python
def _bfs(self, start, goal, avoid_ghosts=True):
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        (curr, path) = queue.popleft()
        
        if curr == goal:
            return path
        
        for direction in [(0,1), (1,0), (0,-1), (-1,0)]:
            next_pos = (curr[0] + direction[0], curr[1] + direction[1])
            
            if (0 <= next_pos[0] < self.num_rows and
                0 <= next_pos[1] < self.num_cols and
                next_pos not in visited and
                self._is_walkable(next_pos, avoid_ghosts)):
                
                visited.add(next_pos)
                queue.append((next_pos, path + [next_pos]))
    
    return []  # 无路径
```

**危险评估：**
```python
def _assess_danger(self, grid_pos):
    min_dist = float('inf')
    nearest_ghost = None
    
    for ghost in self.ghost_manager.ghosts_list:
        if not ghost.is_scared:
            ghost_grid = self._pixel_to_grid((ghost.rect.x, ghost.rect.y))
            dist = self._manhattan_distance(grid_pos, ghost_grid)
            
            if dist < min_dist:
                min_dist = dist
                nearest_ghost = ghost_grid
    
    # 距离 → 危险等级映射
    if min_dist <= 2:
        danger_level = 10
    elif min_dist <= 5:
        danger_level = 9 - (min_dist - 3)
    # ...
    
    return danger_level, nearest_ghost
```

## 性能测试结果

**30 秒测试统计：**
- 游戏时长：29.2 秒
- 总帧数：832
- 平均 FPS：28.51
- 最终分数：440
- 决策分布：
  - 逃跑（flee）：466 次（56.0%）
  - 吃豆（eat）：234 次（28.1%）
  - 追击（chase）：132 次（15.9%）
  - 空闲（idle）：0 次（0.0%）

**分析：**
1. AI 能够正常运行并得分
2. 生存优先策略明显（56% 时间逃跑）
3. 能够利用能量豆反击（15.9% 追击）
4. 积极寻找豆子（28.1% 吃豆）
5. FPS 稳定在 28-30，性能良好

## 优化建议

### 短期优化

1. **调整危险阈值**
   - 当前：danger_level > 6 时逃跑
   - 建议：根据关卡难度动态调整（4-8）

2. **改进路径规划**
   - 考虑幽灵移动预测
   - 添加多条路径评估（避免死胡同）

3. **优化吃豆策略**
   - 优先吃能量豆（当幽灵密集时）
   - 考虑豆子的价值（普通豆 vs 能量豆）

### 长期优化

1. **机器学习方法**
   - 使用强化学习训练 AI
   - 从人类玩家数据学习策略

2. **多智能体协作**
   - 如果有多个吃豆人，实现协作策略
   - 分工合作（一个引开幽灵，其他吃豆）

3. **高级寻路算法**
   - A* 算法替代 BFS
   - 添加启发式函数（考虑幽灵位置）

## 文件结构

```
PyPacman/
├── src/
│   └── ai/
│       ├── __init__.py          # 模块导出
│       ├── pacman_ai.py         # AI 决策引擎
│       └── visualizer.py        # 可视化调试
├── ai_main.py                   # AI 模式入口
├── test_ai.py                   # 测试脚本
└── docs/
    └── AI_README.md             # 本文档
```

## API 参考

### PacmanAI 类

```python
class PacmanAI:
    def __init__(self, game_state: GameState, matrix: list, ghost_manager):
        """
        初始化 AI。
        
        Args:
            game_state: 游戏状态对象
            matrix: 迷宫矩阵（引用）
            ghost_manager: GhostManager 实例
        """
    
    def decide_direction(self, pacman_pos: Tuple[int, int], 
                        pacman_direction: str) -> str:
        """
        决策：应该往哪个方向移动。
        
        Args:
            pacman_pos: 吃豆人位置 (pixel_x, pixel_y)
            pacman_direction: 当前方向 'l'/'r'/'u'/'d'
        
        Returns:
            建议的方向 'l'/'r'/'u'/'d'
        """
    
    def get_debug_info(self) -> dict:
        """
        获取调试信息。
        
        Returns:
            {
                'current_target': (row, col),
                'path': [(row, col), ...],
                'decision': 'flee'/'chase'/'eat'/'idle',
                'danger_level': 0-10,
                'nearest_dot': (row, col),
            }
        """
```

### AIVisualizer 类

```python
class AIVisualizer:
    def __init__(self, screen: Surface):
        """
        初始化可视化器。
        
        Args:
            screen: pygame 显示 Surface
        """
    
    def draw(self, debug_info: dict, pacman_pos: Tuple[int, int]):
        """
        绘制调试信息。
        
        Args:
            debug_info: AI 的调试信息字典
            pacman_pos: 吃豆人位置 (pixel_x, pixel_y)
        """
```

## 常见问题

**Q: AI 为什么总是逃跑？**
A: 这是设计决策，优先保证生存。可以调整 `_assess_danger` 中的危险阈值。

**Q: AI 能否通关？**
A: 当前版本能在 30 秒内获得 440 分，但还未完成第一关。需要优化路径规划和策略。

**Q: 如何关闭可视化调试？**
A: 在 `ai_main.py` 中注释掉 `self.draw_debug_info()` 调用。

**Q: AI 支持哪些关卡？**
A: 目前只测试了 level1.json。理论上支持所有关卡，但可能需要针对不同关卡调整参数。

## 参考资料

- BFS 算法：[Breadth-first search - Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
- A* 算法：[A* search algorithm - Wikipedia](https://en.wikipedia.org/wiki/A*_search_algorithm)
- pygame 文档：[pygame documentation](https://www.pygame.org/docs/)
- 吃豆人游戏机制：[Pac-Man game mechanics](https://gamefaqs.gamespot.com/arcade/563202-pac-man/faqs/56489)

## 许可证

本项目遵循原 PyPacman 项目的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 AI 玩家！
