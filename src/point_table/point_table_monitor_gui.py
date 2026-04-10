#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
点位表可视化监控程序
实时显示PLC所有点位数据
"""

import sys
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

import pandas as pd
import snap7
from snap7.util import *
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QPushButton, QLabel, QGroupBox, QScrollArea,
                             QStatusBar, QHeaderView, QSplitter)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QColor, QFont
from loguru import logger
import yaml


@dataclass
class PointInfo:
    """点位信息"""
    name: str
    db_number: int
    byte_offset: int
    bit_offset: int = 0
    data_type: str = "REAL"
    size: int = 4

    @classmethod
    def from_address(cls, name: str, address: str, data_type: str) -> 'PointInfo':
        """从地址字符串解析点位信息"""
        match = re.match(r'DB(\d+)\.(\d+)\.(\d+)', address)
        if not match:
            raise ValueError(f"无效的地址格式: {address}")

        db_num = int(match.group(1))
        byte_off = int(match.group(2))
        bit_off = int(match.group(3))

        if data_type == "REAL":
            size = 4
        elif data_type == "BOOL":
            size = 1
        elif data_type == "INT":
            size = 2
        elif data_type == "DINT":
            size = 4
        else:
            size = 4

        return cls(name=name, db_number=db_num, byte_offset=byte_off,
                  bit_offset=bit_off, data_type=data_type, size=size)


class PointTableMonitor(QMainWindow):
    """点位表监控主窗口"""

    def __init__(self):
        super().__init__()
        self.points: List[PointInfo] = []
        self.client = snap7.client.Client()
        self.is_connected = False
        self.is_monitoring = False
        self.data_cache: Dict[str, any] = {}

        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'real_count': 0,
            'bool_count': 0
        }

        self.init_ui()
        self.load_point_table()

    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("PLC点位表可视化监控")
        self.setGeometry(100, 100, 1200, 800)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)

        # 控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel)

        # 统计信息面板
        stats_panel = self.create_stats_panel()
        main_layout.addWidget(stats_panel)

        # 数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["序号", "点位名称", "地址", "数据类型", "当前值"])

        # 设置表格样式
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #444;
                background-color: #1e1e1e;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
            }
            QHeaderView::section {
                background-color: #3c3c3c;
                color: white;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
            }
        """)

        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # 设置行高
        self.table.verticalHeader().setDefaultSectionSize(30)

        main_layout.addWidget(self.table)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)

    def create_control_panel(self):
        """创建控制面板"""
        group = QGroupBox("控制面板")
        layout = QHBoxLayout()

        # 连接按钮
        self.connect_btn = QPushButton("连接PLC")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_btn)

        # 开始监控按钮
        self.monitor_btn = QPushButton("开始监控")
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a5c8a;
            }
        """)
        self.monitor_btn.clicked.connect(self.toggle_monitoring)
        self.monitor_btn.setEnabled(False)
        layout.addWidget(self.monitor_btn)

        # 刷新按钮
        refresh_btn = QPushButton("单次刷新")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        refresh_btn.clicked.connect(self.single_refresh)
        refresh_btn.setEnabled(False)
        self.refresh_btn = refresh_btn
        layout.addWidget(refresh_btn)

        # 清除按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        clear_btn.clicked.connect(self.clear_data)
        layout.addWidget(clear_btn)

        # PLC IP显示
        self.ip_label = QLabel("PLC: 192.168.0.1")
        self.ip_label.setStyleSheet("color: #888; padding: 8px;")
        layout.addWidget(self.ip_label)

        layout.addStretch()
        group.setLayout(layout)
        return group

    def create_stats_panel(self):
        """创建统计信息面板"""
        group = QGroupBox("统计信息")
        layout = QHBoxLayout()

        self.stats_labels = {}

        stats_config = [
            ('total', '总点数', '#2196F3'),
            ('success', '读取成功', '#4CAF50'),
            ('failed', '读取失败', '#f44336'),
            ('real_count', 'REAL类型', '#FF9800'),
            ('bool_count', 'BOOL类型', '#9C27B0')
        ]

        for key, label, color in stats_config:
            stat_label = QLabel(f"{label}: 0")
            stat_label.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 100px;
                }}
            """)
            layout.addWidget(stat_label)
            self.stats_labels[key] = stat_label

        layout.addStretch()
        group.setLayout(layout)
        return group

    def load_point_table(self):
        """加载点位表"""
        try:
            df = pd.read_excel(PROJECT_ROOT / 'data' / '点位表.xlsx')

            for idx, row in df.iterrows():
                name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                addr = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
                dtype = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""

                if not addr or addr == "nan" or addr == "NaN":
                    continue

                try:
                    point = PointInfo.from_address(name, addr, dtype)
                    self.points.append(point)
                except:
                    pass

            # 填充表格
            self.table.setRowCount(len(self.points))
            for idx, point in enumerate(self.points):
                self.set_row_data(idx, point)

            # 更新统计
            self.stats['total'] = len(self.points)
            self.stats['real_count'] = sum(1 for p in self.points if p.data_type == 'REAL')
            self.stats['bool_count'] = sum(1 for p in self.points if p.data_type == 'BOOL')
            self.update_stats_display()

            self.status_bar.showMessage(f"已加载 {len(self.points)} 个点位")

        except Exception as e:
            self.status_bar.showMessage(f"加载点位表失败: {e}")

    def set_row_data(self, idx: int, point: PointInfo, value=None):
        """设置表格行数据"""
        # 序号
        item0 = QTableWidgetItem(str(idx + 1))
        item0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 0, item0)

        # 点位名称
        item1 = QTableWidgetItem(point.name)
        self.table.setItem(idx, 1, item1)

        # 地址
        addr = f"DB{point.db_number}.{point.byte_offset}.{point.bit_offset}"
        item2 = QTableWidgetItem(addr)
        item2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 2, item2)

        # 数据类型
        item3 = QTableWidgetItem(point.data_type)
        item3.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 3, item3)

        # 当前值
        if value is not None:
            item4 = QTableWidgetItem(str(value))
            if point.data_type == "BOOL":
                if value:
                    item4.setBackground(QColor(76, 175, 80))
                    item4.setForeground(QColor(255, 255, 255))
                else:
                    item4.setBackground(QColor(158, 158, 158))
                    item4.setForeground(QColor(255, 255, 255))
            else:
                item4.setBackground(QColor(33, 150, 243))
                item4.setForeground(QColor(255, 255, 255))
        else:
            item4 = QTableWidgetItem("--")
            item4.setForeground(QColor(100, 100, 100))

        item4.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(idx, 4, item4)

    def toggle_connection(self):
        """切换连接状态"""
        if not self.is_connected:
            self.connect_to_plc()
        else:
            self.disconnect_from_plc()

    def connect_to_plc(self):
        """连接到PLC"""
        try:
            self.client.connect("192.168.0.1", 0, 1)
            self.is_connected = True
            self.connect_btn.setText("断开连接")
            self.connect_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    padding: 8px 16px;
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
            self.monitor_btn.setEnabled(True)
            self.refresh_btn.setEnabled(True)
            self.status_bar.showMessage("✅ PLC连接成功")
        except Exception as e:
            self.status_bar.showMessage(f"❌ 连接失败: {e}")

    def disconnect_from_plc(self):
        """断开PLC连接"""
        self.timer.stop()
        self.is_monitoring = False
        self.monitor_btn.setText("开始监控")

        try:
            self.client.disconnect()
        except:
            pass

        self.is_connected = False
        self.connect_btn.setText("连接PLC")
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.monitor_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.status_bar.showMessage("已断开连接")

    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_btn.setText("停止监控")
            self.timer.start(1000)  # 1秒刷新一次
            self.status_bar.showMessage("🔍 开始监控...")
        else:
            self.is_monitoring = False
            self.monitor_btn.setText("开始监控")
            self.timer.stop()
            self.status_bar.showMessage("⏸ 停止监控")

    def single_refresh(self):
        """单次刷新"""
        self.update_data()

    def update_data(self):
        """更新数据"""
        if not self.is_connected:
            return

        success_count = 0
        failed_count = 0

        # 按DB块分组
        db_groups = {}
        for point in self.points:
            if point.db_number not in db_groups:
                db_groups[point.db_number] = []
            db_groups[point.db_number].append(point)

        # 读取数据
        for db_num, points in db_groups.items():
            max_offset = max(p.byte_offset + p.size for p in points)

            try:
                raw_data = self.client.db_read(db_num, 0, max_offset)

                for point in points:
                    try:
                        if point.data_type == "REAL":
                            value = get_real(raw_data, point.byte_offset)
                        elif point.data_type == "BOOL":
                            value = get_bool(raw_data, point.byte_offset, point.bit_offset)
                        elif point.data_type == "INT":
                            value = get_int(raw_data, point.byte_offset)
                        elif point.data_type == "DINT":
                            value = get_dint(raw_data, point.byte_offset)
                        else:
                            value = None

                        # 更新表格
                        idx = self.points.index(point)
                        self.set_row_data(idx, point, value)
                        self.data_cache[point.name] = value
                        success_count += 1

                    except Exception as e:
                        failed_count += 1
                        logger.debug(f"读取失败 {point.name}: {e}")

            except Exception as e:
                logger.debug(f"读取DB{db_num}失败: {e}")
                for point in points:
                    failed_count += 1

        # 更新统计
        self.stats['success'] = success_count
        self.stats['failed'] = failed_count
        self.update_stats_display()

        self.status_bar.showMessage(f"✅ 更新完成 | 成功: {success_count} 失败: {failed_count}")

    def update_stats_display(self):
        """更新统计显示"""
        self.stats_labels['total'].setText(f"总点数: {self.stats['total']}")
        self.stats_labels['success'].setText(f"读取成功: {self.stats['success']}")
        self.stats_labels['failed'].setText(f"读取失败: {self.stats['failed']}")
        self.stats_labels['real_count'].setText(f"REAL类型: {self.stats['real_count']}")
        self.stats_labels['bool_count'].setText(f"BOOL类型: {self.stats['bool_count']}")

    def clear_data(self):
        """清除数据显示"""
        for idx, point in enumerate(self.points):
            self.set_row_data(idx, point, None)

        self.stats['success'] = 0
        self.stats['failed'] = 0
        self.update_stats_display()
        self.status_bar.showMessage("已清除数据")

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_connected:
            try:
                self.client.disconnect()
            except:
                pass
        event.accept()


def main():
    app = QApplication(sys.argv)

    # 设置应用样式
    app.setStyle('Fusion')

    window = PointTableMonitor()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
