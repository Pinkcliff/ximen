#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
点位表可视化监控程序 v2
仅读取PLC数据，分组布局，后台线程通信，数据变化变色闪烁
"""

import sys
import time
from pathlib import Path
from datetime import datetime

if getattr(sys, 'frozen', False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).parent.parent.parent

import pandas as pd
import snap7
from snap7.util import *
import re
import yaml
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QStatusBar, QHeaderView, QSplitter,
    QDoubleSpinBox, QMessageBox, QFrame,
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from loguru import logger


# ---------------------------------------------------------------------------
#  Data Model
# ---------------------------------------------------------------------------

@dataclass
class PointInfo:
    name: str
    db_number: int
    byte_offset: int
    bit_offset: int = 0
    data_type: str = "REAL"
    size: int = 4

    _SIZES = {"REAL": 4, "BOOL": 1, "INT": 2, "DINT": 4, "WORD": 2, "DWORD": 4}

    @classmethod
    def from_address(cls, name: str, address: str, data_type: str) -> "PointInfo":
        m = re.match(r"DB(\d+)\.(\d+)\.(\d+)", address)
        if not m:
            raise ValueError(f"无效的地址格式: {address}")
        return cls(
            name=name,
            db_number=int(m.group(1)),
            byte_offset=int(m.group(2)),
            bit_offset=int(m.group(3)),
            data_type=data_type,
            size=cls._SIZES.get(data_type, 4),
        )

    @property
    def address(self) -> str:
        return f"DB{self.db_number}.{self.byte_offset}.{self.bit_offset}"


# ---------------------------------------------------------------------------
#  Background PLC Reader
# ---------------------------------------------------------------------------

class PLCReader(QThread):
    """后台PLC读取线程，支持持续监控和单次刷新"""

    data_ready = pyqtSignal(dict, int, int)  # {db_num: {name: val}}, ok, fail
    connection_status = pyqtSignal(bool, str)  # connected, msg

    def __init__(
        self,
        plc_ip: str,
        rack: int,
        slot: int,
        points: List[PointInfo],
        refresh_interval: float = 1.0,
        single_shot: bool = False,
    ):
        super().__init__()
        self.plc_ip = plc_ip
        self.rack = rack
        self.slot = slot
        self.points = points
        self.refresh_interval = refresh_interval
        self.single_shot = single_shot
        self._client: Optional[snap7.client.Client] = None
        self._running = False

    # -- thread entry --

    def run(self):
        self._running = True

        try:
            self._client = snap7.client.Client()
            self._client.connect(self.plc_ip, self.rack, self.slot)
            self.connection_status.emit(True, f"已连接 {self.plc_ip}")
        except Exception as e:
            self.connection_status.emit(False, str(e))
            return

        if self.single_shot:
            res, s, f = self._read_all()
            self.data_ready.emit(res, s, f)
        else:
            while self._running:
                res, s, f = self._read_all()
                if self._running:
                    self.data_ready.emit(res, s, f)
                t = 0.0
                while t < self.refresh_interval and self._running:
                    time.sleep(0.05)
                    t += 0.05

        try:
            if self._client:
                self._client.disconnect()
        except Exception:
            pass
        self.connection_status.emit(False, "已断开连接")

    def stop(self):
        self._running = False

    # -- internal --

    def _read_all(self) -> Tuple[Dict[int, Dict[str, any]], int, int]:
        if not self._client:
            return {}, 0, 0

        groups: Dict[int, List[PointInfo]] = {}
        for p in self.points:
            groups.setdefault(p.db_number, []).append(p)

        results: Dict[int, Dict[str, any]] = {}
        ok = fail = 0

        for db, pts in groups.items():
            max_off = max(p.byte_offset + p.size for p in pts)
            try:
                raw = self._client.db_read(db, 0, max_off)
                vals = {}
                for p in pts:
                    try:
                        vals[p.name] = self._parse(raw, p)
                        ok += 1
                    except Exception:
                        vals[p.name] = None
                        fail += 1
                results[db] = vals
            except Exception:
                results[db] = {p.name: None for p in pts}
                fail += len(pts)

        return results, ok, fail

    @staticmethod
    def _parse(data: bytes, p: PointInfo):
        if p.data_type == "REAL":
            return get_real(data, p.byte_offset)
        if p.data_type == "BOOL":
            return get_bool(data, p.byte_offset, p.bit_offset)
        if p.data_type == "INT":
            return get_int(data, p.byte_offset)
        if p.data_type == "DINT":
            return get_dint(data, p.byte_offset)
        if p.data_type == "WORD":
            return get_word(data, p.byte_offset)
        if p.data_type == "DWORD":
            return get_dword(data, p.byte_offset)
        return None


class _ConnectTester(QThread):
    """异步连接测试线程"""

    result = pyqtSignal(bool, str)

    def __init__(self, ip: str, rack: int, slot: int):
        super().__init__()
        self.ip = ip
        self.rack = rack
        self.slot = slot

    def run(self):
        try:
            c = snap7.client.Client()
            c.connect(self.ip, self.rack, self.slot)
            c.disconnect()
            self.result.emit(True, f"已连接 {self.ip}")
        except Exception as e:
            self.result.emit(False, str(e))


# ---------------------------------------------------------------------------
#  Styles
# ---------------------------------------------------------------------------

FLASH_MS = 600
CLR_UP = QColor(200, 245, 200)
CLR_DOWN = QColor(245, 200, 200)
CLR_FAIL = QColor(230, 230, 230)
CLR_CLEAR = QColor(0, 0, 0, 0)


def _btn_style(normal: str, hover: str) -> str:
    return f"QPushButton {{ background: {normal}; color: white; padding: 6px 14px; border: none; border-radius: 4px; font-weight: bold; font-size: 13px; }} QPushButton:hover {{ background: {hover}; }} QPushButton:disabled {{ background: #bbb; color: #666; }}"


BTN_GREEN = _btn_style("#4CAF50", "#45a049")
BTN_RED = _btn_style("#f44336", "#da190b")
BTN_BLUE = _btn_style("#2196F3", "#0b7dda")
BTN_ORANGE = _btn_style("#FF9800", "#e68900")


# ---------------------------------------------------------------------------
#  Main Window
# ---------------------------------------------------------------------------

class PointTableMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.points: List[PointInfo] = []
        self.db_groups: Dict[int, List[PointInfo]] = {}
        self.prev_values: Dict[str, any] = {}
        self._flash_timers: Dict[int, QTimer] = {}
        self.reader: Optional[PLCReader] = None
        self._single_reader: Optional[PLCReader] = None
        self._connect_tester: Optional[_ConnectTester] = None
        self.is_connected = False
        self.is_monitoring = False
        self.selected_db: Optional[int] = None
        self.config: dict = {}

        self._load_config()
        self._load_points()
        self._build_ui()

    # ---- config / data ----

    def _load_config(self):
        path = PROJECT_ROOT / "config" / "batch_config.yaml"
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except Exception:
            self.config = {}

    @property
    def _plc_ip(self) -> str:
        return self.config.get("plc", {}).get("ip_address", "192.168.0.1")

    @property
    def _rack(self) -> int:
        return self.config.get("plc", {}).get("rack", 0)

    @property
    def _slot(self) -> int:
        return self.config.get("plc", {}).get("slot", 1)

    @property
    def _default_interval(self) -> float:
        return self.config.get("reading", {}).get("refresh_interval", 1.0)

    def _load_points(self):
        path = PROJECT_ROOT / "data" / "point_table.xlsx"
        try:
            df = pd.read_excel(path)
        except Exception as e:
            QMessageBox.critical(None, "错误", f"无法加载点位表:\n{e}")
            return

        for _, row in df.iterrows():
            name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            addr = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            dtype = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""
            if not addr or addr.lower() == "nan":
                continue
            try:
                pt = PointInfo.from_address(name, addr, dtype)
                self.points.append(pt)
                self.db_groups.setdefault(pt.db_number, []).append(pt)
            except Exception:
                pass

        logger.info(f"加载 {len(self.points)} 个点位, {len(self.db_groups)} 个DB块")

    # ---- UI construction ----

    def _build_ui(self):
        self.setWindowTitle("PLC点位监控")
        self.setGeometry(100, 100, 1200, 800)

        root = QWidget()
        self.setCentralWidget(root)
        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        vbox.addWidget(self._build_toolbar())

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_db_panel())
        splitter.addWidget(self._build_table())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 1000])
        vbox.addWidget(splitter, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(f"就绪 | 已加载 {len(self.points)} 个点位")

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)

        self.led = QLabel("●")
        self.led.setFixedWidth(20)
        self.led.setStyleSheet("color: #f44336; font-size: 18px; font-weight: bold;")
        row.addWidget(self.led)

        self.btn_connect = QPushButton("连接")
        self.btn_connect.setStyleSheet(BTN_GREEN)
        self.btn_connect.clicked.connect(self._on_connect)
        row.addWidget(self.btn_connect)

        self._sep(row)

        self.btn_monitor = QPushButton("开始监控")
        self.btn_monitor.setStyleSheet(BTN_BLUE)
        self.btn_monitor.clicked.connect(self._on_monitor)
        self.btn_monitor.setEnabled(False)
        row.addWidget(self.btn_monitor)

        row.addWidget(QLabel("间隔:"))
        self.spin_interval = QDoubleSpinBox()
        self.spin_interval.setRange(0.5, 10.0)
        self.spin_interval.setValue(self._default_interval)
        self.spin_interval.setSingleStep(0.5)
        self.spin_interval.setSuffix(" 秒")
        self.spin_interval.setFixedWidth(90)
        row.addWidget(self.spin_interval)

        self._sep(row)

        self.btn_refresh = QPushButton("单次刷新")
        self.btn_refresh.setStyleSheet(BTN_ORANGE)
        self.btn_refresh.clicked.connect(self._on_refresh)
        self.btn_refresh.setEnabled(False)
        row.addWidget(self.btn_refresh)

        row.addStretch()

        ip_lbl = QLabel(f"PLC: {self._plc_ip}")
        ip_lbl.setStyleSheet("color: #666;")
        row.addWidget(ip_lbl)

        return bar

    @staticmethod
    def _sep(layout):
        s = QFrame()
        s.setFrameShape(QFrame.VLine)
        s.setStyleSheet("color: #ccc;")
        layout.addWidget(s)

    def _build_db_panel(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("DB块列表")
        lbl.setStyleSheet("font-weight: bold; padding: 4px; font-size: 13px;")
        vbox.addWidget(lbl)

        self.db_list = QListWidget()
        item_all = QListWidgetItem(f"全部 ({len(self.points)})")
        item_all.setData(Qt.UserRole, None)
        self.db_list.addItem(item_all)

        for db in sorted(self.db_groups):
            cnt = len(self.db_groups[db])
            it = QListWidgetItem(f"DB{db} ({cnt})")
            it.setData(Qt.UserRole, db)
            self.db_list.addItem(it)

        self.db_list.setCurrentRow(0)
        self.db_list.currentItemChanged.connect(self._on_db_changed)
        vbox.addWidget(self.db_list)
        return w

    def _build_table(self) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["序号", "点位名称", "地址", "数据类型", "当前值", "变化"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in (2, 3, 4, 5):
            hdr.setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(28)

        self._fill_table()
        vbox.addWidget(self.table)
        return w

    # ---- table helpers ----

    def _visible_points(self) -> List[PointInfo]:
        if self.selected_db is None:
            return self.points
        return self.db_groups.get(self.selected_db, [])

    def _fill_table(self):
        pts = self._visible_points()
        self.table.setRowCount(len(pts))
        for i, p in enumerate(pts):
            self._write_row(i, p)

    def _write_row(self, row: int, pt: PointInfo, value=None, prev=None):
        self.table.setItem(row, 0, self._ci(str(row + 1)))
        self.table.setItem(row, 1, QTableWidgetItem(pt.name))
        self.table.setItem(row, 2, self._ci(pt.address))
        self.table.setItem(row, 3, self._ci(pt.data_type))

        # value
        if value is not None:
            vi = self._ci(str(value))
            if pt.data_type == "BOOL":
                vi.setBackground(QColor(76, 175, 80) if value else QColor(100, 100, 100))
                vi.setForeground(QColor(255, 255, 255))
            else:
                vi.setForeground(QColor(230, 230, 230))
        else:
            vi = self._ci("--")
            vi.setForeground(QColor(100, 100, 100))
        self.table.setItem(row, 4, vi)

        # change
        ci = self._ci("")
        if value is not None and prev is not None:
            try:
                if pt.data_type == "BOOL":
                    if value != prev:
                        ci.setText("●")
                        ci.setForeground(QColor(255, 193, 7))
                elif isinstance(value, (int, float)) and isinstance(prev, (int, float)):
                    d = value - prev
                    if d > 0:
                        ci.setText(f"↑+{d:.3g}")
                        ci.setForeground(QColor(76, 175, 80))
                    elif d < 0:
                        ci.setText(f"↓{d:.3g}")
                        ci.setForeground(QColor(244, 67, 54))
            except (TypeError, ValueError):
                pass
        self.table.setItem(row, 5, ci)

    def _ci(self, text: str) -> QTableWidgetItem:
        it = QTableWidgetItem(text)
        it.setTextAlignment(Qt.AlignCenter)
        return it

    def _flash_row(self, row: int, color: QColor):
        for c in range(self.table.columnCount()):
            it = self.table.item(row, c)
            if it:
                it.setBackground(color)
        if row in self._flash_timers:
            self._flash_timers[row].stop()
        t = QTimer(self)
        t.setSingleShot(True)
        t.timeout.connect(lambda r=row: self._unflash(r))
        t.start(FLASH_MS)
        self._flash_timers[row] = t

    def _unflash(self, row: int):
        for c in range(self.table.columnCount()):
            it = self.table.item(row, c)
            if it:
                it.setBackground(CLR_CLEAR)

    # ---- UI state ----

    def _set_connected(self, connected: bool):
        self.is_connected = connected
        if connected:
            self.btn_connect.setText("断开")
            self.btn_connect.setStyleSheet(BTN_RED)
            self.led.setStyleSheet("color: #4CAF50; font-size: 18px; font-weight: bold;")
            self.btn_monitor.setEnabled(True)
            self.btn_refresh.setEnabled(True)
        else:
            self.btn_connect.setText("连接")
            self.btn_connect.setStyleSheet(BTN_GREEN)
            self.led.setStyleSheet("color: #f44336; font-size: 18px;")
            self.btn_monitor.setEnabled(False)
            self.btn_refresh.setEnabled(False)

    def _set_monitoring(self, on: bool):
        self.is_monitoring = on
        if on:
            self.btn_monitor.setText("停止监控")
            self.btn_monitor.setStyleSheet(BTN_RED)
            self.btn_refresh.setEnabled(False)
            self.btn_connect.setEnabled(False)
            self.spin_interval.setEnabled(False)
        else:
            self.btn_monitor.setText("开始监控")
            self.btn_monitor.setStyleSheet(BTN_BLUE)
            if self.is_connected:
                self.btn_refresh.setEnabled(True)
                self.btn_connect.setEnabled(True)
            self.spin_interval.setEnabled(True)

    # ---- actions ----

    def _on_connect(self):
        if self.is_connected:
            self._do_disconnect()
        else:
            self._do_connect()

    def _do_connect(self):
        self.btn_connect.setEnabled(False)
        self.status.showMessage("正在连接...")
        self._connect_tester = _ConnectTester(self._plc_ip, self._rack, self._slot)
        self._connect_tester.result.connect(self._on_connect_result)
        self._connect_tester.start()

    def _on_connect_result(self, ok: bool, msg: str):
        self._set_connected(ok)
        if not ok:
            QMessageBox.warning(self, "连接失败", msg)
        self.status.showMessage(msg)

    def _do_disconnect(self):
        self._stop_monitor()
        self._set_connected(False)
        self.status.showMessage("已断开连接")

    def _on_monitor(self):
        if self.is_monitoring:
            self._stop_monitor()
        else:
            self._start_monitor()

    def _start_monitor(self):
        self._set_monitoring(True)
        self.status.showMessage("开始监控...")
        self.reader = PLCReader(
            self._plc_ip, self._rack, self._slot,
            self.points, self.spin_interval.value(),
        )
        self.reader.data_ready.connect(self._on_data)
        self.reader.connection_status.connect(self._on_reader_conn)
        self.reader.start()

    def _stop_monitor(self):
        if self.reader:
            self.reader.stop()
            self.reader.wait(3000)
            self.reader = None
        self._set_monitoring(False)

    def _on_reader_conn(self, ok: bool, msg: str):
        if not ok and self.is_monitoring:
            self._stop_monitor()
            self._set_connected(False)
            self.status.showMessage(f"PLC连接断开: {msg}")

    def _on_refresh(self):
        self.btn_refresh.setEnabled(False)
        self.status.showMessage("刷新中...")
        self._single_reader = PLCReader(
            self._plc_ip, self._rack, self._slot,
            self.points, single_shot=True,
        )
        self._single_reader.data_ready.connect(self._on_data)
        self._single_reader.finished.connect(self._on_single_done)
        self._single_reader.start()

    def _on_single_done(self):
        self.btn_refresh.setEnabled(True)

    # ---- data handling ----

    def _on_data(self, results: dict, ok: int, fail: int):
        pts = self._visible_points()
        for i, pt in enumerate(pts):
            val = results.get(pt.db_number, {}).get(pt.name)
            prev = self.prev_values.get(pt.name)

            self._write_row(i, pt, val, prev)

            if val is not None and prev is not None:
                try:
                    if isinstance(val, (int, float)) and isinstance(prev, (int, float)):
                        if val > prev:
                            self._flash_row(i, CLR_UP)
                        elif val < prev:
                            self._flash_row(i, CLR_DOWN)
                except (TypeError, ValueError):
                    pass
            elif val is None and self.prev_values:
                self._flash_row(i, CLR_FAIL)

            self.prev_values[pt.name] = val

        now = datetime.now().strftime("%H:%M:%S")
        self.status.showMessage(f"成功: {ok}  失败: {fail}  |  {now}")

    def _on_db_changed(self, current, _prev):
        if not current:
            return
        self.selected_db = current.data(Qt.UserRole)
        self._fill_table()
        pts = self._visible_points()
        for i, pt in enumerate(pts):
            val = self.prev_values.get(pt.name)
            self._write_row(i, pt, val)

    # ---- cleanup ----

    def closeEvent(self, event):
        if self.reader and self.reader.isRunning():
            self.reader.stop()
            self.reader.wait(3000)
        event.accept()


# ---------------------------------------------------------------------------
#  Entry
# ---------------------------------------------------------------------------

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = PointTableMonitor()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
