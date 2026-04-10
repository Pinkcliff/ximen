#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右缸编码器实时监控 GUI 程序
提供图形界面实时显示右缸编码器位置
"""

import sys
import time
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QLCDNumber, QGroupBox, QGridLayout,
    QTextEdit, QCheckBox, QSlider, QSpinBox, QFrame
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QPalette, QColor, QPixmap
import snap7
from snap7.util import get_real
import pyqtgraph as pg
import numpy as np


class EncoderDataReader(QThread):
    """编码器数据读取线程"""

    data_received = pyqtSignal(float, datetime)  # 位置值和时间戳
    connection_status = pyqtSignal(bool, str)     # 连接状态和错误信息

    def __init__(self, plc_ip="192.168.0.1", rack=0, slot=1, db_number=5, offset=124):
        super().__init__()
        self.plc_ip = plc_ip
        self.rack = rack
        self.slot = slot
        self.db_number = db_number
        self.offset = offset
        self.is_running = False
        self.client = None

    def run(self):
        """线程运行主循环"""
        self.is_running = True

        while self.is_running:
            try:
                # 创建客户端连接
                if self.client is None:
                    self.client = snap7.client.Client()
                    self.client.connect(self.plc_ip, self.rack, self.slot)

                    if self.client.get_connected():
                        self.connection_status.emit(True, "PLC 连接成功")
                    else:
                        self.connection_status.emit(False, "PLC 连接失败")
                        time.sleep(1)
                        continue

                # 读取编码器位置
                data = self.client.db_read(self.db_number, self.offset, 4)
                position = get_real(data, 0)
                current_time = datetime.now()

                # 发送数据
                self.data_received.emit(position, current_time)
                self.connection_status.emit(True, "数据读取正常")

            except Exception as e:
                self.connection_status.emit(False, f"读取错误: {str(e)}")

                # 尝试重新连接
                try:
                    if self.client:
                        self.client.disconnect()
                    self.client = None
                except:
                    pass

                time.sleep(2)

            # 控制读取频率
            self.msleep(100)  # 100ms 读取间隔

    def stop(self):
        """停止线程"""
        self.is_running = False
        try:
            if self.client:
                self.client.disconnect()
        except:
            pass
        self.wait()


class EncoderMonitorGUI(QMainWindow):
    """编码器监控主窗口"""

    def __init__(self):
        super().__init__()
        self.data_reader = None
        self.position_history = []  # 位置历史数据
        self.time_history = []      # 时间历史数据
        self.max_history_points = 1000  # 最大历史数据点数

        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("右缸编码器实时监控系统")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 1. 顶部状态栏
        status_group = self.create_status_group()
        main_layout.addWidget(status_group)

        # 2. 中间主要显示区域
        middle_layout = QHBoxLayout()

        # 左侧：当前位置显示
        left_widget = self.create_position_display()
        middle_layout.addWidget(left_widget, stretch=1)

        # 右侧：实时曲线图
        right_widget = self.create_chart()
        middle_layout.addWidget(right_widget, stretch=2)

        main_layout.addLayout(middle_layout, stretch=3)

        # 3. 底部控制区域
        control_layout = QHBoxLayout()

        # 控制按钮
        control_widget = self.create_control_panel()
        control_layout.addWidget(control_widget)

        # 统计信息
        stats_widget = self.create_stats_panel()
        control_layout.addWidget(stats_widget)

        main_layout.addLayout(control_layout, stretch=1)

        # 4. 底部日志区域
        log_group = self.create_log_panel()
        main_layout.addWidget(log_group, stretch=1)

        # 设置定时器更新统计信息
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_statistics)
        self.stats_timer.start(1000)  # 每秒更新统计信息

        # 记录开始时间
        self.start_time = datetime.now()

    def create_status_group(self):
        """创建状态显示组"""
        group = QGroupBox("连接状态")
        layout = QHBoxLayout()

        self.status_label = QLabel("未连接")
        self.status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.connection_time_label = QLabel("")
        layout.addWidget(self.connection_time_label)

        layout.addStretch()

        return group

    def create_position_display(self):
        """创建位置显示面板"""
        group = QGroupBox("右缸编码器当前位置")
        layout = QVBoxLayout()

        # 当前位置 - 使用 LCD 数字显示
        self.position_lcd = QLCDNumber()
        self.position_lcd.setDigitCount(10)
        self.position_lcd.setFixedSize(300, 100)
        self.position_lcd.setStyleSheet("""
            QLCDNumber {
                background-color: #2E3440;
                color: #88C0D0;
                border: 2px solid #4C566A;
                border-radius: 5px;
            }
        """)
        self.position_lcd.display(0.000)
        layout.addWidget(self.position_lcd, alignment=Qt.AlignmentFlag.AlignCenter)

        # 单位标签
        unit_label = QLabel("mm (毫米)")
        unit_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        unit_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(unit_label)

        # 位置变化指示器
        self.change_indicator = QLabel("●")
        self.change_indicator.setStyleSheet("color: gray; font-size: 24px;")
        self.change_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.change_indicator)

        layout.addStretch()
        return group

    def create_chart(self):
        """创建实时曲线图"""
        group = QGroupBox("位置变化曲线")
        layout = QVBoxLayout()

        # 创建 pyqtgraph 绘图组件
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#2E3440")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', '位置', units='mm', color='#D8DEE9')
        self.plot_widget.setLabel('bottom', '时间', units='s', color='#D8DEE9')

        # 创建曲线
        self.plot_curve = self.plot_widget.plot(pen=pg.mkPen(color='#88C0D0', width=2))

        # 设置坐标轴范围
        self.plot_widget.setXRange(0, 60)  # 显示最近60秒
        self.plot_widget.setYRange(-10, 10)  # 初始范围

        layout.addWidget(self.plot_widget)

        return group

    def create_control_panel(self):
        """创建控制面板"""
        group = QGroupBox("控制面板")
        layout = QVBoxLayout()

        # 开始/停止按钮
        self.start_btn = QPushButton("开始监控")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)
        self.start_btn.clicked.connect(self.toggle_monitoring)
        layout.addWidget(self.start_btn)

        # 清除历史数据按钮
        clear_btn = QPushButton("清除历史数据")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #BF616A;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
        """)
        clear_btn.clicked.connect(self.clear_history)
        layout.addWidget(clear_btn)

        # 读取频率设置
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("读取频率:"))

        self.freq_slider = QSlider(Qt.Orientation.Horizontal)
        self.freq_slider.setRange(10, 1000)
        self.freq_slider.setValue(100)
        self.freq_slider.valueChanged.connect(self.update_frequency)
        freq_layout.addWidget(self.freq_slider)

        self.freq_label = QLabel("100 ms")
        freq_layout.addWidget(self.freq_label)

        layout.addLayout(freq_layout)

        # 位置阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("变化阈值:"))

        self.threshold_spinbox = QSpinBox()
        self.threshold_spinbox.setRange(1, 1000)
        self.threshold_spinbox.setValue(1)
        self.threshold_spinbox.setSuffix(" mm")
        threshold_layout.addWidget(self.threshold_spinbox)

        layout.addLayout(threshold_layout)

        # 添加垂直拉伸
        layout.addStretch()
        return group

    def create_stats_panel(self):
        """创建统计信息面板"""
        group = QGroupBox("统计信息")
        layout = QGridLayout()

        # 当前位置
        layout.addWidget(QLabel("当前位置:"), 0, 0)
        self.current_pos_label = QLabel("0.000 mm")
        self.current_pos_label.setStyleSheet("font-weight: bold; color: #88C0D0;")
        layout.addWidget(self.current_pos_label, 0, 1)

        # 最大值
        layout.addWidget(QLabel("最大值:"), 1, 0)
        self.max_pos_label = QLabel("0.000 mm")
        self.max_pos_label.setStyleSheet("font-weight: bold; color: #A3BE8C;")
        layout.addWidget(self.max_pos_label, 1, 1)

        # 最小值
        layout.addWidget(QLabel("最小值:"), 2, 0)
        self.min_pos_label = QLabel("0.000 mm")
        self.min_pos_label.setStyleSheet("font-weight: bold; color: #BF616A;")
        layout.addWidget(self.min_pos_label, 2, 1)

        # 平均值
        layout.addWidget(QLabel("平均值:"), 3, 0)
        self.avg_pos_label = QLabel("0.000 mm")
        self.avg_pos_label.setStyleSheet("font-weight: bold; color: #EBCB8B;")
        layout.addWidget(self.avg_pos_label, 3, 1)

        # 变化次数
        layout.addWidget(QLabel("位置变化:"), 4, 0)
        self.change_count_label = QLabel("0 次")
        self.change_count_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.change_count_label, 4, 1)

        # 运行时间
        layout.addWidget(QLabel("运行时间:"), 5, 0)
        self.runtime_label = QLabel("00:00:00")
        self.runtime_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.runtime_label, 5, 1)

        # 添加垂直拉伸
        layout.setRowStretch(6, 1)
        return group

    def create_log_panel(self):
        """创建日志面板"""
        group = QGroupBox("日志信息")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #3B4252;
                color: #D8DEE9;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_text)

        return group

    def toggle_monitoring(self):
        """切换监控状态"""
        if self.data_reader is None or not self.data_reader.isRunning():
            self.start_monitoring()
        else:
            self.stop_monitoring()

    def start_monitoring(self):
        """开始监控"""
        try:
            self.data_reader = EncoderDataReader()
            self.data_reader.data_received.connect(self.on_data_received)
            self.data_reader.connection_status.connect(self.on_connection_status)
            self.data_reader.start()

            self.start_btn.setText("停止监控")
            self.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #BF616A;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #D08770;
                }
            """)

            self.start_time = datetime.now()
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 开始监控右缸编码器位置...")

        except Exception as e:
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 启动监控失败: {e}")

    def stop_monitoring(self):
        """停止监控"""
        if self.data_reader:
            self.data_reader.stop()
            self.data_reader = None

        self.start_btn.setText("开始监控")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #5E81AC;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #81A1C1;
            }
        """)

        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 监控已停止")

    def on_data_received(self, position, timestamp):
        """接收到数据时的处理"""
        # 更新位置显示
        self.position_lcd.display(position)

        # 添加到历史数据
        self.position_history.append(position)
        self.time_history.append(timestamp)

        # 限制历史数据长度
        if len(self.position_history) > self.max_history_points:
            self.position_history.pop(0)
            self.time_history.pop(0)

        # 更新当前位置标签
        self.current_pos_label.setText(f"{position:.3f} mm")

        # 检测位置变化
        if len(self.position_history) >= 2:
            prev_pos = self.position_history[-2]
            threshold = self.threshold_spinbox.value()

            if abs(position - prev_pos) >= threshold:
                self.change_indicator.setStyleSheet("color: #A3BE8C; font-size: 24px;")
                self.change_count_label.setText(f"{int(self.change_count_label.text().split()[0]) + 1} 次")

                # 记录变化到日志
                self.log_text.append(f"[{timestamp.strftime('%H:%M:%S')}] 位置变化: {prev_pos:.3f} → {position:.3f} mm")

                # 2秒后恢复指示器颜色
                QTimer.singleShot(2000, lambda: self.change_indicator.setStyleSheet("color: gray; font-size: 24px;"))

    def on_connection_status(self, connected, message):
        """连接状态更新"""
        if connected:
            self.status_label.setText(f"✅ {message}")
            self.status_label.setStyleSheet("color: #A3BE8C; font-size: 16px; font-weight: bold;")
        else:
            self.status_label.setText(f"❌ {message}")
            self.status_label.setStyleSheet("color: #BF616A; font-size: 16px; font-weight: bold;")

    def update_statistics(self):
        """更新统计信息"""
        if not self.position_history:
            return

        # 计算统计值
        positions = np.array(self.position_history)
        max_pos = np.max(positions)
        min_pos = np.min(positions)
        avg_pos = np.mean(positions)

        # 更新标签
        self.max_pos_label.setText(f"{max_pos:.3f} mm")
        self.min_pos_label.setText(f"{min_pos:.3f} mm")
        self.avg_pos_label.setText(f"{avg_pos:.3f} mm")

        # 更新运行时间
        if hasattr(self, 'start_time'):
            runtime = datetime.now() - self.start_time
            hours, remainder = divmod(runtime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        # 更新图表
        self.update_chart()

    def update_chart(self):
        """更新实时曲线图"""
        if len(self.time_history) < 2:
            return

        # 计算时间轴（相对时间，秒）
        start_time = self.time_history[0]
        time_seconds = [(t - start_time).total_seconds() for t in self.time_history]

        # 更新曲线数据
        self.plot_curve.setData(time_seconds, self.position_history)

        # 自动调整 X 轴范围
        if time_seconds[-1] > 60:
            self.plot_widget.setXRange(time_seconds[-1] - 60, time_seconds[-1])
        else:
            self.plot_widget.setXRange(0, 60)

        # 自动调整 Y 轴范围
        if self.position_history:
            min_val = min(self.position_history)
            max_val = max(self.position_history)
            margin = (max_val - min_val) * 0.1 + 1
            self.plot_widget.setYRange(min_val - margin, max_val + margin)

    def clear_history(self):
        """清除历史数据"""
        self.position_history.clear()
        self.time_history.clear()
        self.plot_curve.setData([], [])
        self.change_count_label.setText("0 次")
        self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 历史数据已清除")

    def update_frequency(self, value):
        """更新读取频率"""
        self.freq_label.setText(f"{value} ms")
        if self.data_reader:
            self.data_reader.msleep(value)

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.stop_monitoring()
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle('Fusion')

    # 设置暗色主题
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
    app.setPalette(palette)

    window = EncoderMonitorGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()