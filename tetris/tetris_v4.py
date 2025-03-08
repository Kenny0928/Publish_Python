import sys
import random
import json
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QGridLayout, 
                            QPushButton, QLabel, QDesktopWidget, QVBoxLayout, 
                            QHBoxLayout, QWidget, QMessageBox)
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QBrush

# 顏色定義
COLORS = [
    0x1A1A1A,  # 深灰色（背景）
    0xFF5555,  # 紅色 (Z形方塊)
    0x55FF55,  # 綠色 (S形方塊)
    0x5555FF,  # 藍色 (J形方塊)
    0xFFFF55,  # 黃色 (O形方塊)
    0xFF55FF,  # 紫色 (T形方塊)
    0x55FFFF,  # 青色 (I形方塊)
    0xFF9933,  # 橙色 (L形方塊)
]

# 背景和邊界顏色
BACKGROUND_COLOR = QColor(0x121212)  # 更深的背景色
GRID_LINE_COLOR = QColor(0x303030)  # 網格線顏色
BORDER_COLOR = QColor(0x4D4D4D)  # 邊界顏色

# 方塊形狀定義
SHAPES = [
    [[0, 0, 0, 0],  # 空白
     [0, 0, 0, 0],
     [0, 0, 0, 0],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # Z形方塊
     [0, 1, 1, 0],
     [0, 0, 1, 1],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # S形方塊
     [0, 0, 2, 2],
     [0, 2, 2, 0],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # J形方塊
     [0, 3, 0, 0],
     [0, 3, 3, 3],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # O形方塊
     [0, 4, 4, 0],
     [0, 4, 4, 0],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # T形方塊
     [0, 0, 5, 0],
     [0, 5, 5, 5],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # I形方塊
     [0, 0, 0, 0],
     [6, 6, 6, 6],
     [0, 0, 0, 0]],

    [[0, 0, 0, 0],  # L形方塊
     [0, 0, 0, 7],
     [0, 7, 7, 7],
     [0, 0, 0, 0]]
]

# Super Rotation System (SRS) 牆踢數據
# 每種方塊的旋轉測試點，除了 O 形方塊
# 格式: [順時針旋轉測試點, 逆時針旋轉測試點]
# 每個旋轉測試點包含 5 個可能的位置偏移 (x, y)
SRS_WALL_KICKS = {
    # JLSTZ 形方塊的牆踢數據
    'JLSTZ': [
        # 0>>1, 1>>2, 2>>3, 3>>0 (順時針旋轉)
        [
            [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],  # 0>>1
            [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    # 1>>2
            [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     # 2>>3
            [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]  # 3>>0
        ],
        # 0>>3, 3>>2, 2>>1, 1>>0 (逆時針旋轉)
        [
            [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],     # 0>>3
            [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],    # 3>>2
            [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],  # 2>>1
            [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)]  # 1>>0
        ]
    ],
    # I 形方塊的牆踢數據
    'I': [
        # 0>>1, 1>>2, 2>>3, 3>>0 (順時針旋轉)
        [
            [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)],   # 0>>1
            [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],   # 1>>2
            [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],   # 2>>3
            [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)]    # 3>>0
        ],
        # 0>>3, 3>>2, 2>>1, 1>>0 (逆時針旋轉)
        [
            [(0, 0), (-1, 0), (2, 0), (-1, -2), (2, 1)],   # 0>>3
            [(0, 0), (2, 0), (-1, 0), (2, -1), (-1, 2)],   # 3>>2
            [(0, 0), (1, 0), (-2, 0), (1, 2), (-2, -1)],   # 2>>1
            [(0, 0), (-2, 0), (1, 0), (-2, 1), (1, -2)]    # 1>>0
        ]
    ],
    # O 形方塊不需要牆踢
    'O': [
        [[(0, 0)], [(0, 0)], [(0, 0)], [(0, 0)]],
        [[(0, 0)], [(0, 0)], [(0, 0)], [(0, 0)]]
    ]
}

# 方塊類型映射
SHAPE_TYPES = {
    1: 'JLSTZ',  # Z
    2: 'JLSTZ',  # S
    3: 'JLSTZ',  # J
    4: 'O',      # O
    5: 'JLSTZ',  # T
    6: 'I',      # I
    7: 'JLSTZ'   # L
}

class TetrisBoard(QFrame):
    """俄羅斯方塊的主遊戲區域"""
    
    # 發送信號到父視窗，表示需要更新下一個方塊顯示
    nextPieceSignal = pyqtSignal(list)
    # 發送分數更新信號
    scoreChangedSignal = pyqtSignal(int)
    # 發送遊戲狀態變更信號 (開始/結束)
    statusChangedSignal = pyqtSignal(bool)
    # 發送難度變更信號
    levelChangedSignal = pyqtSignal(int)
    # 發送儲存方塊變更信號
    holdPieceSignal = pyqtSignal(dict)
    
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 22  # 上面兩行為緩衝區，不顯示
    INITIAL_SPEED = 500  # 初始速度，毫秒
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # 初始化所有屬性
        self.timer = QBasicTimer()
        self.landingTimer = QBasicTimer()
        self.isStarted = False
        self.isPaused = False
        self.score = 0
        self.level = 1
        self.linesCleared = 0
        self.board = []
        self.curPiece = {'shape': 0, 'x': 0, 'y': 0, 'rotation': 0}
        self.nextPieces = []
        self.board_left = 0
        self.board_top = 0
        self.square_size = 0
        self.speed = self.INITIAL_SPEED
        self.shakeOffset = 0  # 添加振動偏移屬性
        
        # 儲存方塊相關屬性
        self.holdPiece = {'shape': 0, 'rotation': 0}  # 儲存的方塊
        self.hasSwapped = False  # 是否已經在本次下落中交換過方塊
        
        # 設定遊戲區域大小
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setFocusPolicy(Qt.StrongFocus)
        
        try:
            self.initBoard()
        except Exception as e:
            print(f"初始化遊戲區域時發生錯誤: {e}")
            # 在實際應用中，可以顯示錯誤對話框或記錄到日誌
    
    def initBoard(self):
        """初始化遊戲區域"""
        self.isStarted = False
        self.isPaused = False
        self.score = 0
        self.level = 1
        self.linesCleared = 0
        self.speed = self.INITIAL_SPEED
        
        self.clearBoard()
        
        # 初始化當前和下一個方塊
        self.curPiece = self.getNewPiece()
        self.nextPieces = [self.getNewPiece() for _ in range(3)]
        self.nextPieceSignal.emit(self.nextPieces)
        
        # 初始化儲存方塊
        self.holdPiece = {'shape': 0, 'rotation': 0}
        self.hasSwapped = False
        self.holdPieceSignal.emit(self.holdPiece)
        
    def clearBoard(self):
        """清空遊戲區域"""
        self.board = [[0 for _ in range(self.BOARD_WIDTH)] 
                      for _ in range(self.BOARD_HEIGHT)]
    
    def getNewPiece(self):
        """生成一個新的隨機方塊"""
        shape = random.randint(1, 7)
        return {'shape': shape, 'x': 3, 'y': 0, 'rotation': 0}
    
    def start(self):
        """開始遊戲"""
        if self.isPaused:
            self.isPaused = False
            self.timer.start(self.speed, self)
            self.statusChangedSignal.emit(True)
            return
        
        self.isStarted = True
        self.clearBoard()
        self.score = 0
        self.scoreChangedSignal.emit(self.score)
        
        # 初始化當前和預覽方塊
        self.curPiece = self.getNewPiece()
        self.nextPieces = [self.getNewPiece() for _ in range(3)]
        self.nextPieceSignal.emit(self.nextPieces)
        
        self.timer.start(self.speed, self)
        self.statusChangedSignal.emit(True)
        self.update()
    
    def pause(self):
        """暫停遊戲"""
        if not self.isStarted:
            return
        
        self.isPaused = not self.isPaused
        
        if self.isPaused:
            self.timer.stop()
        else:
            self.timer.start(self.speed, self)
        
        self.update()
        self.statusChangedSignal.emit(not self.isPaused)
    
    def paintEvent(self, event):
        """繪製遊戲區域"""
        painter = QPainter(self)
        rect = self.contentsRect()
        
        # 計算方塊大小，確保為正方形
        square_size = min(rect.width() // self.BOARD_WIDTH, 
                         rect.height() // (self.BOARD_HEIGHT - 2))
        self.square_size = square_size
        
        # 計算遊戲區域的左上角位置，使其居中
        board_width = square_size * self.BOARD_WIDTH
        board_height = square_size * (self.BOARD_HEIGHT - 2)
        board_left = rect.left() + (rect.width() - board_width) // 2
        board_top = rect.top() + (rect.height() - board_height) // 2
        
        # 應用振動偏移
        if hasattr(self, 'shakeOffset'):
            board_left += self.shakeOffset
        
        # 繪製背景
        painter.fillRect(rect, BACKGROUND_COLOR)
        
        # 繪製邊界
        pen = painter.pen()
        pen.setColor(BORDER_COLOR)
        pen.setWidth(3)
        painter.setPen(pen)
        painter.drawRect(board_left, board_top, 
                       board_width, 
                       board_height)
        
        # 繪製網格線
        pen.setColor(GRID_LINE_COLOR)
        pen.setWidth(1)
        painter.setPen(pen)
        
        # 繪製垂直網格線
        for i in range(self.BOARD_WIDTH + 1):
            x = board_left + i * square_size
            painter.drawLine(x, board_top, x, board_top + board_height)
        
        # 繪製水平網格線
        for i in range(self.BOARD_HEIGHT - 1):
            y = board_top + i * square_size
            if y >= board_top and y <= board_top + board_height:
                painter.drawLine(board_left, y, board_left + board_width, y)
        
        # 繪製已落下的方塊
        for i in range(self.BOARD_HEIGHT - 2):  # 不繪製上面兩行緩衝區
            for j in range(self.BOARD_WIDTH):
                shape = self.board[i + 2][j]
                
                if shape == 0:
                    continue
                
                # 繪製方塊
                self.drawSquare(painter, board_left + j * square_size,
                              board_top + i * square_size, shape)
        
        # 繪製幽靈方塊（當前方塊落到底部的預覽）
        if self.isStarted and not self.isPaused and self.curPiece['shape']:
            self.drawGhostPiece(painter, board_left, board_top)
        
        # 繪製當前正在下落的方塊
        if self.curPiece['shape']:
            self.drawPiece(painter, board_left, board_top)
            
        # 儲存遊戲區域的位置信息，以便其他方法使用
        self.board_left = board_left
        self.board_top = board_top
    
    def drawPiece(self, painter, x, y):
        """繪製當前下落的方塊"""
        shape_matrix = self.rotatedShape()
        
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                # 使用正確的 y 偏移計算
                row = self.curPiece['y'] + i
                if row >= 2:  # 只繪製可見區域的方塊（非緩衝區）
                    self.drawSquare(painter, 
                                    x + (self.curPiece['x'] + j) * self.squareWidth(),
                                    y + (row - 2) * self.squareHeight(),
                                    shape_matrix[i][j])
    
    def drawSquare(self, painter, x, y, shape):
        """繪製單個方塊"""
        color = QColor(COLORS[shape])
        square_width = self.squareWidth() - 2
        square_height = self.squareHeight() - 2
        
        # 填充方塊主體
        painter.fillRect(x + 1, y + 1, square_width, square_height, color)
        
        # 繪製高光邊緣（左上）
        painter.setPen(color.lighter(150))
        painter.drawLine(x, y, x + square_width, y)
        painter.drawLine(x, y, x, y + square_height)
        
        # 繪製陰影邊緣（右下）
        painter.setPen(color.darker(150))
        painter.drawLine(x + 1, y + square_height,
                       x + square_width + 1, y + square_height)
        painter.drawLine(x + square_width + 1, 
                       y + square_height,
                       x + square_width + 1, y)
                       
        # 繪製內部陰影效果
        gradient = color.darker(120)
        pen = painter.pen()
        pen.setColor(gradient)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(x + 4, y + square_height - 4,
                      x + square_width - 4, y + square_height - 4)
        painter.drawLine(x + square_width - 4, 
                      y + square_height - 4,
                      x + square_width - 4, y + 4)
    
    def squareWidth(self):
        """計算每個小方塊的寬度"""
        if hasattr(self, 'square_size'):
            return self.square_size
        return min(self.contentsRect().width() // self.BOARD_WIDTH,
                  self.contentsRect().height() // (self.BOARD_HEIGHT - 2))
    
    def squareHeight(self):
        """計算每個小方塊的高度"""
        return self.squareWidth()  # 確保方塊是正方形
    
    def timerEvent(self, event):
        """計時器事件，處理方塊下落和振動效果"""
        if event.timerId() == self.timer.timerId():
            # 主遊戲計時器 - 方塊下落
            if self.tryMove({'y': self.curPiece['y'] + 1}):
                pass
            else:
                self.pieceDropped()
        elif hasattr(self, 'landingTimer') and event.timerId() == self.landingTimer.timerId():
            # 落地振動效果計時器
            self.landingEffectEvent()
        else:
            super().timerEvent(event)
    
    def keyPressEvent(self, event):
        """鍵盤事件處理"""
        if not self.isStarted or self.curPiece['shape'] == 0:
            super().keyPressEvent(event)
            return
        
        key = event.key()
        
        if key == Qt.Key_P:
            self.pause()
            return
        
        if self.isPaused:
            return
        
        if key == Qt.Key_Left:
            self.tryMove({'x': self.curPiece['x'] - 1})
        elif key == Qt.Key_Right:
            self.tryMove({'x': self.curPiece['x'] + 1})
        elif key == Qt.Key_Down:
            self.tryMove({'y': self.curPiece['y'] + 1})
        elif key == Qt.Key_Up:
            # 順時針旋轉
            self.tryMove({'rotation': (self.curPiece['rotation'] + 1) % 4})
        elif key == Qt.Key_Z:
            # 逆時針旋轉
            self.tryMove({'rotation': (self.curPiece['rotation'] + 3) % 4})
        elif key == Qt.Key_Space:
            self.dropDown()
        elif key == Qt.Key_Shift:
            # 儲存或交換方塊
            self.swapHoldPiece()
        else:
            super().keyPressEvent(event)
    
    def rotatedShape(self):
        """旋轉方塊"""
        shape_matrix = SHAPES[self.curPiece['shape']]
        
        # 根據旋轉次數旋轉方塊
        for _ in range(self.curPiece['rotation']):
            shape_matrix = self.rotateMatrix(shape_matrix)
            
        return shape_matrix
    
    def rotateMatrix(self, matrix):
        """順時針旋轉矩陣 90 度"""
        # 創建一個新的旋轉後的矩陣
        rotated = [[0 for _ in range(4)] for _ in range(4)]
        
        # 順時針旋轉矩陣
        for i in range(4):
            for j in range(4):
                rotated[j][3-i] = matrix[i][j]
                
        return rotated
    
    def tryMove(self, new_pos):
        """嘗試移動方塊"""
        new_x = new_pos.get('x', self.curPiece['x'])
        new_y = new_pos.get('y', self.curPiece['y'])
        new_rotation = new_pos.get('rotation', self.curPiece['rotation'])
        
        # 檢查是否是旋轉操作
        is_rotation = new_rotation != self.curPiece['rotation']
        
        # 保存當前狀態
        old_x = self.curPiece['x']
        old_y = self.curPiece['y']
        old_rotation = self.curPiece['rotation']
        
        # 如果是旋轉操作，使用 SRS 系統
        if is_rotation and self.curPiece['shape'] > 0:
            # 確定旋轉方向（順時針或逆時針）
            clockwise = (new_rotation - old_rotation) % 4 == 1 or (old_rotation == 3 and new_rotation == 0)
            direction = 0 if clockwise else 1
            
            # 獲取方塊類型
            shape_type = SHAPE_TYPES[self.curPiece['shape']]
            
            # 獲取對應的牆踢數據
            kick_data = SRS_WALL_KICKS[shape_type][direction][old_rotation]
            
            # 嘗試每個可能的牆踢位置
            for kick_x, kick_y in kick_data:
                self.curPiece['x'] = new_x + kick_x
                self.curPiece['y'] = new_y + kick_y
                self.curPiece['rotation'] = new_rotation
                
                shape_matrix = self.rotatedShape()
                if self.checkPosition(shape_matrix):
                    # 找到有效位置，更新並返回
                    self.update()
                    return True
            
            # 所有牆踢位置都無效，恢復原始狀態
            self.curPiece['x'] = old_x
            self.curPiece['y'] = old_y
            self.curPiece['rotation'] = old_rotation
            return False
        else:
            # 非旋轉操作，直接嘗試移動
            self.curPiece['x'] = new_x
            self.curPiece['y'] = new_y
            self.curPiece['rotation'] = new_rotation
            
            shape_matrix = self.rotatedShape()
            if self.checkPosition(shape_matrix):
                self.update()
                return True
            
            # 移動無效，恢復原始狀態
            self.curPiece['x'] = old_x
            self.curPiece['y'] = old_y
            self.curPiece['rotation'] = old_rotation
            return False
    
    def checkPosition(self, shape_matrix):
        """檢查當前位置是否有效"""
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                x = self.curPiece['x'] + j
                y = self.curPiece['y'] + i
                
                if x < 0 or x >= self.BOARD_WIDTH or y >= self.BOARD_HEIGHT:
                    return False
                
                if y < 0:
                    continue
                
                if self.board[y][x] != 0:
                    return False
        
        return True
    
    def dropDown(self):
        """方塊直接落到底部"""
        drop_height = 0
        
        while self.tryMove({'y': self.curPiece['y'] + 1}):
            drop_height += 1
        
        self.pieceDropped()
    
    def pieceDropped(self):
        """方塊落到底部後，在底部固定並生成新方塊"""
        # 將當前方塊的形狀添加到遊戲區域
        shape_matrix = self.rotatedShape()
        
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                x = self.curPiece['x'] + j
                y = self.curPiece['y'] + i
                
                if y < 0:
                    continue
                
                self.board[y][x] = shape_matrix[i][j]
        
        # 添加方塊落地振動效果
        self.addLandingEffect()
        
        # 移除完整的行
        has_full_lines = self.removeFullLines()
        
        # 生成新方塊
        if not self.newPiece():
            self.timer.stop()
            self.isStarted = False
            self.statusChangedSignal.emit(False)
        else:
            # 重置交換標誌，允許在新方塊下落時再次交換
            self.hasSwapped = False
            
        # 確保遊戲區域更新
        self.update()
    
    def addLandingEffect(self):
        """添加方塊落地時的振動效果"""
        # 停止舊計時器（如果存在）
        if hasattr(self, 'landingTimer') and self.landingTimer.isActive():
            self.landingTimer.stop()
            
        # 使用計時器創建短暫的振動效果
        self.landingEffectCount = 0
        self.landingTimer = QBasicTimer()
        self.landingTimer.start(30, self)  # 30毫秒更新一次
        
    def removeFullLines(self):
        """直接移除已填滿的行，不使用閃爍效果"""
        full_lines = []
        
        # 從底部向上檢查每一行，找出需要消除的行
        for i in range(self.BOARD_HEIGHT - 1, -1, -1):
            line_is_full = True
            
            for j in range(self.BOARD_WIDTH):
                if self.board[i][j] == 0:
                    line_is_full = False
                    break
            
            if line_is_full:
                full_lines.append(i)
        
        if full_lines:
            # 直接移除行，不使用閃爍效果
            self.doRemoveLines(full_lines)
            # 強制更新顯示
            self.update()
            return True
        else:
            # 沒有滿行，繼續遊戲
            return False
    
    def doRemoveLines(self, full_lines=None):
        """實際移除已填滿的行"""
        if full_lines is None or not full_lines:
            return
            
        num_full_lines = len(full_lines)
        
        # 確保行索引是從大到小排序的（從底部到頂部）
        full_lines.sort(reverse=True)
        
        # 創建一個新的遊戲區域，不包含滿行
        new_board = [[0 for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        
        # 從底部開始，將非滿行複製到新的遊戲區域
        new_row = self.BOARD_HEIGHT - 1
        for old_row in range(self.BOARD_HEIGHT - 1, -1, -1):
            if old_row in full_lines:
                continue  # 跳過滿行
            
            # 複製這一行到新的遊戲區域
            for j in range(self.BOARD_WIDTH):
                new_board[new_row][j] = self.board[old_row][j]
            
            new_row -= 1
        
        # 更新遊戲區域
        self.board = new_board
        
        # 計算得分：1行=100，2行=300，3行=600，4行=1000
        scores = [0, 100, 300, 600, 1000]
        self.score += scores[min(num_full_lines, 4)]
        self.scoreChangedSignal.emit(self.score)
        
        # 更新消除的行數並檢查是否需要提高難度
        self.linesCleared += num_full_lines
        self.checkLevel()
        
        # 再次檢查是否還有滿行（以防有些行沒被正確識別）
        for i in range(self.BOARD_HEIGHT - 1, -1, -1):
            line_is_full = True
            for j in range(self.BOARD_WIDTH):
                if self.board[i][j] == 0:
                    line_is_full = False
                    break
            
            if line_is_full:
                # 如果還有滿行，遞迴調用自己
                print(f"發現額外的滿行: {i}，再次移除")
                self.removeFullLines()
                break
        
        # 強制重新繪製整個遊戲區域
        self.update()
    
    def checkLevel(self):
        """檢查並更新遊戲難度級別"""
        # 每消除10行提高一個級別，最高10級
        new_level = min(10, 1 + self.linesCleared // 10)
        
        if new_level > self.level:
            self.level = new_level
            # 隨著級別提高，速度增加（速度值減小）
            self.speed = max(100, self.INITIAL_SPEED - (self.level - 1) * 50)
            
            # 如果遊戲正在進行，更新計時器速度
            if self.isStarted and not self.isPaused:
                self.timer.stop()
                self.timer.start(self.speed, self)
            
            # 發送級別變更信號
            self.levelChangedSignal.emit(self.level)
    
    def drawGhostPiece(self, painter, x, y):
        """繪製幽靈方塊（預覽方塊落到底部的位置）"""
        # 保存當前方塊位置
        cur_x = self.curPiece['x']
        cur_y = self.curPiece['y']
        cur_shape = self.curPiece['shape']
        cur_rotation = self.curPiece['rotation']
        
        # 獲取當前旋轉後的方塊形狀
        shape_matrix = self.rotatedShape()
        
        # 計算幽靈方塊位置（方塊直接落到底部的位置）
        ghost_y = cur_y
        
        # 使用更高效的方法計算幽靈方塊位置
        while True:
            ghost_y += 1
            valid = True
            
            # 直接檢查位置有效性，不修改當前方塊狀態
            for i in range(4):
                for j in range(4):
                    if shape_matrix[i][j] == 0:
                        continue
                    
                    new_x = cur_x + j
                    new_y = ghost_y + i
                    
                    if new_x < 0 or new_x >= self.BOARD_WIDTH or new_y >= self.BOARD_HEIGHT:
                        valid = False
                        break
                    
                    if new_y >= 0 and self.board[new_y][new_x] != 0:
                        valid = False
                        break
                
                if not valid:
                    break
            
            if not valid:
                ghost_y -= 1
                break
        
        # 如果幽靈方塊與當前方塊位置相同，不繪製
        if ghost_y == cur_y:
            return
        
        # 繪製幽靈方塊（半透明）
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                # 使用正確的 y 偏移計算
                row = ghost_y + i
                if row >= 2:  # 只繪製可見區域的方塊（非緩衝區）
                    # 使用半透明效果繪製幽靈方塊
                    self.drawGhostSquare(painter, 
                                       x + (cur_x + j) * self.squareWidth(),
                                       y + (row - 2) * self.squareHeight(),
                                       shape_matrix[i][j])
    
    def drawGhostSquare(self, painter, x, y, shape):
        """繪製幽靈方塊的單個方塊（半透明輪廓）"""
        color = QColor(COLORS[shape])
        color.setAlpha(80)  # 設置透明度
        
        square_width = self.squareWidth() - 2
        square_height = self.squareHeight() - 2
        
        # 繪製半透明填充
        painter.fillRect(x + 1, y + 1, square_width, square_height, color)
        
        # 繪製輪廓
        pen = painter.pen()
        pen.setColor(color.lighter(150))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(x + 1, y + 1, square_width, square_height)
        
    def isValidPosition(self, shape, x, y, rotation):
        """檢查指定位置是否有效（用於幽靈方塊計算）"""
        # 保存當前狀態
        old_shape = self.curPiece['shape']
        old_x = self.curPiece['x']
        old_y = self.curPiece['y']
        old_rotation = self.curPiece['rotation']
        
        # 設置臨時狀態
        self.curPiece['shape'] = shape
        self.curPiece['x'] = x
        self.curPiece['y'] = y
        self.curPiece['rotation'] = rotation
        
        shape_matrix = self.rotatedShape()
        
        # 使用 checkPosition 檢查位置有效性
        valid = self.checkPosition(shape_matrix)
        
        # 恢復原始狀態
        self.curPiece['shape'] = old_shape
        self.curPiece['x'] = old_x
        self.curPiece['y'] = old_y
        self.curPiece['rotation'] = old_rotation
        
        return valid
    
    def landingEffectEvent(self):
        """處理落地振動效果"""
        self.landingEffectCount += 1
        
        # 振動3次後停止
        if self.landingEffectCount >= 6:
            self.landingTimer.stop()
            self.shakeOffset = 0  # 重置偏移
            return
        
        # 計算振動偏移量
        self.shakeOffset = 2 if self.landingEffectCount % 2 == 1 else -2
        
        # 更新顯示
        self.update()
    
    def newPiece(self):
        """生成新方塊"""
        self.curPiece = self.nextPieces[0]
        self.nextPieces.pop(0)
        self.nextPieces.append(self.getNewPiece())
        self.nextPieceSignal.emit(self.nextPieces)
        
        # 檢查遊戲是否結束
        # 1. 檢查新方塊是否可以放置
        if not self.tryMove({'x': 3, 'y': 0, 'rotation': 0}):
            self.curPiece = {'shape': 0, 'x': 0, 'y': 0, 'rotation': 0}
            return False
            
        # 2. 檢查頂部區域是否已有方塊（額外的遊戲結束檢查）
        for j in range(self.BOARD_WIDTH):
            if self.board[2][j] != 0:  # 檢查緩衝區下方第一行
                self.curPiece = {'shape': 0, 'x': 0, 'y': 0, 'rotation': 0}
                return False
        
        return True

    def swapHoldPiece(self):
        """儲存當前方塊或與已儲存的方塊交換"""
        # 如果已經在本次下落中交換過，則不允許再次交換
        if self.hasSwapped:
            return
        
        # 保存當前方塊的形狀和旋轉狀態
        current_shape = self.curPiece['shape']
        current_rotation = self.curPiece['rotation']
        
        if self.holdPiece['shape'] == 0:
            # 如果儲存區為空，則儲存當前方塊並生成新方塊
            self.holdPiece = {'shape': current_shape, 'rotation': 0}  # 儲存時重置旋轉狀態
            self.holdPieceSignal.emit(self.holdPiece)
            
            # 生成新方塊
            self.curPiece = self.nextPieces[0]
            self.nextPieces.pop(0)
            self.nextPieces.append(self.getNewPiece())
            self.nextPieceSignal.emit(self.nextPieces)
        else:
            # 如果儲存區有方塊，則交換
            temp_shape = self.holdPiece['shape']
            self.holdPiece = {'shape': current_shape, 'rotation': 0}  # 儲存時重置旋轉狀態
            self.holdPieceSignal.emit(self.holdPiece)
            
            # 設置當前方塊為儲存的方塊
            self.curPiece = {'shape': temp_shape, 'x': 3, 'y': 0, 'rotation': 0}
        
        # 檢查新位置是否有效
        if not self.tryMove({'x': 3, 'y': 0, 'rotation': 0}):
            # 如果新位置無效，遊戲結束
            self.timer.stop()
            self.isStarted = False
            self.statusChangedSignal.emit(False)
            return
        
        # 標記已經交換過
        self.hasSwapped = True
        
        # 更新顯示
        self.update()


class NextPieceDisplay(QFrame):
    """顯示下一個方塊的視窗"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setFixedSize(180, 350)  # 調整預覽區的大小
        self.nextPieces = [{'shape': 0}, {'shape': 0}, {'shape': 0}]
    
    def updateNextPieces(self, next_pieces):
        """更新下一個方塊"""
        self.nextPieces = next_pieces
        self.update()
    
    def paintEvent(self, event):
        """繪製下一個方塊"""
        painter = QPainter(self)
        rect = self.contentsRect()
        
        # 繪製背景
        painter.fillRect(rect, BACKGROUND_COLOR)
        
        # 繪製邊界
        pen = painter.pen()
        pen.setColor(BORDER_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # 繪製標題
        pen.setColor(Qt.white)
        painter.setPen(pen)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect.left() + 10, rect.top() + 20, "下一個方塊")
        
        # 繪製分隔線
        painter.setPen(BORDER_COLOR)
        painter.drawLine(rect.left() + 5, rect.top() + 30, 
                       rect.right() - 5, rect.top() + 30)
        
        # 分別繪製三個預覽方塊，每個都有邊框
        for i, piece in enumerate(self.nextPieces):
            piece_top = rect.top() + 40 + i * 100  # 減少方塊間距
            
            # 繪製方塊區域背景和邊框
            painter.setPen(BORDER_COLOR)
            box_size = 90  # 減小預覽框的大小
            painter.drawRect(rect.left() + 45, piece_top, box_size, box_size)
            
            # 根據方塊形狀調整中心位置
            shape_width = 0
            shape_height = 0
            if piece['shape'] > 0:
                shape_matrix = SHAPES[piece['shape']]
                # 計算實際形狀的寬度和高度
                min_x, max_x, min_y, max_y = 4, 0, 4, 0
                for i in range(4):
                    for j in range(4):
                        if shape_matrix[i][j] > 0:
                            min_x = min(min_x, j)
                            max_x = max(max_x, j)
                            min_y = min(min_y, i)
                            max_y = max(max_y, i)
                
                shape_width = max_x - min_x + 1
                shape_height = max_y - min_y + 1
            
            # 計算居中位置，一個方塊單元格大小為18
            square_size = 18
            x_offset = rect.left() + 45 + (box_size - shape_width * square_size) // 2
            y_offset = piece_top + (box_size - shape_height * square_size) // 2
            
            self.drawPiece(painter, x_offset, y_offset, piece['shape'])
    
    def drawPiece(self, painter, x, y, shape):
        """繪製方塊"""
        if shape == 0:
            return
            
        shape_matrix = SHAPES[shape]
        
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                self.drawSquare(painter, x + j * 18, y + i * 18, 
                                shape_matrix[i][j])
    
    def drawSquare(self, painter, x, y, shape):
        """繪製單個方塊"""
        color = QColor(COLORS[shape])
        
        painter.fillRect(x + 1, y + 1, 16, 16, color)
        
        painter.setPen(color.lighter())
        painter.drawLine(x, y + 16, x, y)
        painter.drawLine(x, y, x + 16, y)
        
        painter.setPen(color.darker())
        painter.drawLine(x + 1, y + 16, x + 16, y + 16)
        painter.drawLine(x + 16, y + 16, x + 16, y + 1)


class HoldPieceDisplay(QFrame):
    """顯示儲存方塊的視窗"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.setFixedSize(180, 150)  # 調整儲存區的大小
        self.holdPiece = {'shape': 0, 'rotation': 0}
    
    def updateHoldPiece(self, hold_piece):
        """更新儲存的方塊"""
        self.holdPiece = hold_piece
        self.update()
    
    def paintEvent(self, event):
        """繪製儲存的方塊"""
        painter = QPainter(self)
        rect = self.contentsRect()
        
        # 繪製背景
        painter.fillRect(rect, BACKGROUND_COLOR)
        
        # 繪製邊界
        pen = painter.pen()
        pen.setColor(BORDER_COLOR)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(rect.adjusted(1, 1, -1, -1))
        
        # 繪製標題
        pen.setColor(Qt.white)
        painter.setPen(pen)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(rect.left() + 10, rect.top() + 20, "儲存方塊")
        
        # 繪製分隔線
        painter.setPen(BORDER_COLOR)
        painter.drawLine(rect.left() + 5, rect.top() + 30, 
                       rect.right() - 5, rect.top() + 30)
        
        # 繪製方塊區域背景和邊框
        painter.setPen(BORDER_COLOR)
        box_size = 90  # 調整大小
        painter.drawRect(rect.left() + 45, rect.top() + 40, box_size, box_size)
        
        # 如果有儲存的方塊，繪製它
        if self.holdPiece['shape'] > 0:
            shape_matrix = SHAPES[self.holdPiece['shape']]
            
            # 計算實際形狀的寬度和高度
            min_x, max_x, min_y, max_y = 4, 0, 4, 0
            for i in range(4):
                for j in range(4):
                    if shape_matrix[i][j] > 0:
                        min_x = min(min_x, j)
                        max_x = max(max_x, j)
                        min_y = min(min_y, i)
                        max_y = max(max_y, i)
            
            shape_width = max_x - min_x + 1
            shape_height = max_y - min_y + 1
            
            # 計算居中位置，一個方塊單元格大小為18
            square_size = 18
            x_offset = rect.left() + 45 + (box_size - shape_width * square_size) // 2
            y_offset = rect.top() + 40 + (box_size - shape_height * square_size) // 2
            
            self.drawPiece(painter, x_offset, y_offset, self.holdPiece['shape'])
    
    def drawPiece(self, painter, x, y, shape):
        """繪製方塊"""
        if shape == 0:
            return
            
        shape_matrix = SHAPES[shape]
        
        for i in range(4):
            for j in range(4):
                if shape_matrix[i][j] == 0:
                    continue
                
                self.drawSquare(painter, x + j * 18, y + i * 18, 
                                shape_matrix[i][j])
    
    def drawSquare(self, painter, x, y, shape):
        """繪製單個方塊"""
        color = QColor(COLORS[shape])
        
        painter.fillRect(x + 1, y + 1, 16, 16, color)
        
        painter.setPen(color.lighter())
        painter.drawLine(x, y + 16, x, y)
        painter.drawLine(x, y, x + 16, y)
        
        painter.setPen(color.darker())
        painter.drawLine(x + 1, y + 16, x + 16, y + 16)
        painter.drawLine(x + 16, y + 16, x + 16, y + 1)


class TetrisWindow(QMainWindow):
    """俄羅斯方塊遊戲視窗"""
    
    def __init__(self):
        super().__init__()
        
        # 初始化遊戲記錄
        self.highScore = 0
        self.loadGameRecord()
        
        self.initUI()
    
    def initUI(self):
        """初始化UI"""
        self.board = TetrisBoard(self)
        self.nextPieceDisplay = NextPieceDisplay(self)
        self.holdPieceDisplay = HoldPieceDisplay(self)  # 新增儲存方塊顯示區
        
        # 連接信號和槽
        self.board.nextPieceSignal.connect(self.nextPieceDisplay.updateNextPieces)
        self.board.scoreChangedSignal.connect(self.updateScore)
        self.board.statusChangedSignal.connect(self.updateStatus)
        self.board.levelChangedSignal.connect(self.updateLevel)
        self.board.holdPieceSignal.connect(self.holdPieceDisplay.updateHoldPiece)  # 連接儲存方塊信號
        
        # 創建控制部分
        self.createControlPanel()
        
        # 主佈局
        mainLayout = QHBoxLayout()
        mainLayout.addWidget(self.board, 7)  # 設置比例為7
        
        # 右側佈局
        rightLayout = QVBoxLayout()
        rightLayout.addWidget(self.holdPieceDisplay)  # 添加儲存方塊顯示區
        rightLayout.addWidget(self.nextPieceDisplay)
        rightLayout.addWidget(self.controlPanel)
        rightLayout.setStretchFactor(self.holdPieceDisplay, 1)
        rightLayout.setStretchFactor(self.nextPieceDisplay, 3)
        rightLayout.setStretchFactor(self.controlPanel, 2)
        
        mainLayout.addLayout(rightLayout, 3)  # 設置比例為3
        
        # 設定中央視窗
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        centralWidget.setStyleSheet("background-color: #121212; color: white;")
        self.setCentralWidget(centralWidget)
        
        # 遊戲結束覆蓋層
        self.gameOverOverlay = QLabel(self.board)
        self.gameOverOverlay.setAlignment(Qt.AlignCenter)
        self.gameOverOverlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid #FF5555;
            border-radius: 10px;
        """)
        self.gameOverOverlay.setText("遊戲結束\n點擊開始新遊戲")
        self.gameOverOverlay.hide()
        
        # 暫停覆蓋層
        self.pauseOverlay = QLabel(self.board)
        self.pauseOverlay.setAlignment(Qt.AlignCenter)
        self.pauseOverlay.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            font-size: 24px;
            font-weight: bold;
            border: 2px solid #FFCC44;
            border-radius: 10px;
        """)
        self.pauseOverlay.setText("遊戲暫停")
        self.pauseOverlay.hide()
        
        # 設定視窗
        self.setWindowTitle('俄羅斯方塊')
        self.resize(600, 600)  # 調整視窗初始大小
        self.setMinimumSize(500, 500)  # 設置最小視窗大小
        self.center()
        
        # 設置整體深色主題
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #121212;
                color: white;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            QPushButton:pressed {
                background-color: #666666;
            }
            QLabel {
                color: white;
            }
            QFrame {
                border: 2px solid #555555;
                background-color: #1A1A1A;
            }
        """)
        
        self.show()
    
    def createControlPanel(self):
        """創建控制面板"""
        self.controlPanel = QFrame(self)
        self.controlPanel.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.controlPanel.setMinimumHeight(180)  # 設置最小高度
        
        # 開始按鈕
        self.startButton = QPushButton('開始遊戲', self)
        self.startButton.setFocusPolicy(Qt.NoFocus)
        self.startButton.clicked.connect(self.startGame)
        self.startButton.setMinimumHeight(30)
        self.startButton.setStyleSheet("""
            QPushButton {
                background-color: #2A7422;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3A8532;
            }
        """)
        
        # 暫停按鈕
        self.pauseButton = QPushButton('暫停', self)
        self.pauseButton.setFocusPolicy(Qt.NoFocus)
        self.pauseButton.clicked.connect(self.pauseGame)
        self.pauseButton.setMinimumHeight(30)
        self.pauseButton.setStyleSheet("""
            QPushButton {
                background-color: #7A5420;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8A6430;
            }
        """)
        
        # 分數和狀態顯示框
        infoFrame = QFrame()
        infoFrame.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        infoFrame.setStyleSheet("background-color: #222222; padding: 10px;")
        
        # 分數顯示
        self.scoreLabel = QLabel('分數: 0')
        self.scoreLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFCC44;")
        
        # 最高分顯示
        self.highScoreLabel = QLabel(f'最高分: {self.highScore}')
        self.highScoreLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF55FF;")
        
        # 級別顯示
        self.levelLabel = QLabel('級別: 1')
        self.levelLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #55FF55;")
        
        # 狀態顯示
        self.statusLabel = QLabel('按下開始遊戲')
        self.statusLabel.setStyleSheet("font-size: 12px; color: #AAAAAA;")
        
        # 操作說明標籤
        controlsLabel = QLabel(
            "控制說明:\n"
            "← → : 左右移動\n"
            "↑ : 順時針旋轉\n"
            "Z : 逆時針旋轉\n"
            "↓ : 加速下落\n"
            "空白鍵 : 直接落下\n"
            "Shift : 儲存/交換方塊\n"
            "P : 暫停遊戲"
        )
        controlsLabel.setStyleSheet("color: #AAAAAA; font-size: 10px; margin-top: 5px;")  # 調整字體大小
        
        # 資訊框佈局
        infoLayout = QVBoxLayout()
        infoLayout.addWidget(self.scoreLabel)
        infoLayout.addWidget(self.highScoreLabel)
        infoLayout.addWidget(self.levelLabel)
        infoLayout.addWidget(self.statusLabel)
        infoFrame.setLayout(infoLayout)
        
        # 控制面板佈局
        layout = QVBoxLayout()
        layout.addWidget(self.startButton)
        layout.addWidget(self.pauseButton)
        layout.addWidget(infoFrame)
        layout.addWidget(controlsLabel)
        layout.addStretch()
        
        self.controlPanel.setLayout(layout)
    
    def startGame(self):
        """開始遊戲"""
        self.board.start()
        self.gameOverOverlay.hide()
        self.pauseOverlay.hide()
    
    def pauseGame(self):
        """暫停遊戲"""
        self.board.pause()
        
        # 更新暫停覆蓋層
        if self.board.isPaused and self.board.isStarted:
            self.updatePauseOverlay()
            self.pauseOverlay.show()
        else:
            self.pauseOverlay.hide()
    
    def updateScore(self, score):
        """更新分數顯示"""
        self.scoreLabel.setText(f'分數: {score}')
        
        # 檢查是否創造新的最高分
        if score > self.highScore:
            self.highScore = score
            self.highScoreLabel.setText(f'最高分: {self.highScore}')
            self.saveGameRecord()
    
    def updateLevel(self, level):
        """更新級別顯示"""
        self.levelLabel.setText(f'級別: {level}')
    
    def updateStatus(self, isStarted):
        """更新遊戲狀態顯示"""
        if isStarted:
            self.statusLabel.setText('遊戲進行中')
            self.gameOverOverlay.hide()
        else:
            self.statusLabel.setText('遊戲結束')
            self.updateGameOverOverlay()
            self.gameOverOverlay.show()
            
            # 檢查是否創造新的最高分
            if self.board.score > 0:
                if self.board.score >= self.highScore:
                    QMessageBox.information(self, '恭喜', f'恭喜您創造了新的最高分: {self.board.score}!')
                else:
                    QMessageBox.information(self, '遊戲結束', f'您的分數: {self.board.score}\n最高分: {self.highScore}')
    
    def updateGameOverOverlay(self):
        """更新遊戲結束覆蓋層"""
        # 調整覆蓋層大小以適應遊戲區域
        self.gameOverOverlay.setGeometry(self.board.rect())
        
        # 顯示最終分數和最高分
        if self.board.score >= self.highScore:
            self.gameOverOverlay.setText(f"遊戲結束\n最終分數: {self.board.score}\n新的最高分!\n點擊開始新遊戲")
        else:
            self.gameOverOverlay.setText(f"遊戲結束\n最終分數: {self.board.score}\n最高分: {self.highScore}\n點擊開始新遊戲")
    
    def updatePauseOverlay(self):
        """更新暫停覆蓋層"""
        # 調整覆蓋層大小以適應遊戲區域
        self.pauseOverlay.setGeometry(self.board.rect())
    
    def resizeEvent(self, event):
        """視窗大小變更事件"""
        super().resizeEvent(event)
        
        # 調整覆蓋層大小
        if hasattr(self, 'gameOverOverlay') and self.board.isVisible():
            self.gameOverOverlay.setGeometry(self.board.rect())
        
        if hasattr(self, 'pauseOverlay') and self.board.isVisible():
            self.pauseOverlay.setGeometry(self.board.rect())
    
    def center(self):
        """使視窗居中顯示"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def loadGameRecord(self):
        """載入遊戲記錄"""
        try:
            # 檢查記錄文件是否存在
            if os.path.exists('tetris_record.json'):
                with open('tetris_record.json', 'r') as f:
                    record = json.load(f)
                    self.highScore = record.get('high_score', 0)
            else:
                # 創建新記錄文件
                self.saveGameRecord()
        except FileNotFoundError:
            print("記錄文件不存在，將創建新文件")
            self.highScore = 0
            self.saveGameRecord()
        except PermissionError:
            print("無權限讀取記錄文件")
            QMessageBox.warning(self, '錯誤', '無權限讀取遊戲記錄文件')
            self.highScore = 0
        except json.JSONDecodeError:
            print("記錄文件格式錯誤")
            QMessageBox.warning(self, '錯誤', '遊戲記錄文件格式錯誤')
            self.highScore = 0
        except Exception as e:
            print(f"載入遊戲記錄時發生錯誤: {e}")
            self.highScore = 0
    
    def saveGameRecord(self):
        """保存遊戲記錄"""
        try:
            record = {
                'high_score': self.highScore
            }
            with open('tetris_record.json', 'w') as f:
                json.dump(record, f)
        except PermissionError:
            print("無權限寫入記錄文件")
            QMessageBox.warning(self, '錯誤', '無權限保存遊戲記錄')
        except IOError:
            print("寫入記錄文件時發生IO錯誤")
            QMessageBox.warning(self, '錯誤', '保存遊戲記錄時發生IO錯誤')
        except Exception as e:
            print(f"保存遊戲記錄時發生錯誤: {e}")
            QMessageBox.warning(self, '錯誤', '無法保存遊戲記錄')
    
    def closeEvent(self, event):
        """視窗關閉事件"""
        # 保存遊戲記錄
        self.saveGameRecord()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TetrisWindow()
    sys.exit(app.exec_())