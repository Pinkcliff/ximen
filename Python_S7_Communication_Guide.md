# Python 西门子 S7 通信开发指南

## 📋 项目概述

基于 Python 3.11.13 实现上位机与西门子 PLC 的 TCP/IP 通信，通过 S7 协议读取博途（TIA Portal）DB 块数据。

---

## 🛠️ 开发环境准备

### Python 版本
- **Python**: 3.11.13
- **操作系统**: Windows 10/11
- **IDE**: 推荐使用 PyCharm 或 VSCode

### 依赖库安装

```bash
# 核心通信库
pip install python-snap7

# 辅助工具库
pip install pyqt6 matplotlib pandas numpy

# 日志和调试
pip install loguru pyyaml

# 网络工具
pip install netifaces
```

### 验证安装

```python
import snap7
print(f"Snap7 版本: {snap7.__version__}")
```

---

## 🔧 PLC 侧配置

### 1. TIA Portal 设置

1. **启用 PUT/GET 通信**
   - 打开 TIA Portal 项目
   - 进入「设备组态」→「以太网接口」→「属性」
   - 勾选「允许来自远程对象的PUT/GET通信访问」

2. **DB 块设置**
   - 创建非优化 DB 块（重要！）
   - 记录关键参数：
     ```
     DB 块编号: 1
     起始地址: 0 (对应 DB1.DBW0)
     数据类型: Int (2字节)
     数据长度: 2 字节
     ```

3. **网络配置**
   - PLC IP: 192.168.0.1
   - 子网掩码: 255.255.255.0
   - 确保与上位机在同一网段

### 2. 关键参数表

| 参数项 | 取值示例 | 说明 |
|--------|----------|------|
| PLC IP 地址 | 192.168.0.1 | PLC 的网络地址 |
| 机架号 | 0 | S7-1200 默认值 |
| 槽位号 | 1 | S7-1200 默认值 |
| DB 块编号 | DB1 | 要读取的数据块 |
| 起始地址 | 0 | DB 块内的字节偏移 |
| 数据长度 | 2 | 读取的字节数 |

---

## 💻 Python 核心实现

### 1. 基础连接类

```python
import snap7
from snap7.util import *
import time
from loguru import logger
from typing import Optional, Union, List, Dict

class S7PLCConnector:
    """西门子 S7 PLC 连接器"""

    def __init__(self, ip_address: str, rack: int = 0, slot: int = 1):
        """
        初始化 PLC 连接器

        Args:
            ip_address: PLC IP 地址
            rack: 机架号，默认 0
            slot: 槽位号，默认 1
        """
        self.ip_address = ip_address
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.is_connected = False

    def connect(self) -> bool:
        """连接到 PLC"""
        try:
            self.client.connect(self.ip_address, self.rack, self.slot)
            self.is_connected = True
            logger.info(f"成功连接到 PLC: {self.ip_address}")
            return True
        except Exception as e:
            logger.error(f"连接 PLC 失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            self.client.disconnect()
            self.is_connected = False
            logger.info("已断开 PLC 连接")

    def read_db(self, db_number: int, start_offset: int, size: int) -> Optional[bytes]:
        """
        读取 DB 块数据

        Args:
            db_number: DB 块编号
            start_offset: 起始偏移量（字节）
            size: 读取的字节数

        Returns:
            bytes: 读取的数据，失败返回 None
        """
        if not self.is_connected:
            logger.error("未连接到 PLC")
            return None

        try:
            data = self.client.db_read(db_number, start_offset, size)
            logger.debug(f"读取 DB{db_number}.DB{start_offset} 成功，数据长度: {size} 字节")
            return data
        except Exception as e:
            logger.error(f"读取 DB 块失败: {e}")
            return None

    def write_db(self, db_number: int, start_offset: int, data: bytes) -> bool:
        """
        写入 DB 块数据

        Args:
            db_number: DB 块编号
            start_offset: 起始偏移量（字节）
            data: 要写入的数据

        Returns:
            bool: 写入成功返回 True
        """
        if not self.is_connected:
            logger.error("未连接到 PLC")
            return False

        try:
            self.client.db_write(db_number, start_offset, data)
            logger.info(f"写入 DB{db_number}.DB{start_offset} 成功")
            return True
        except Exception as e:
            logger.error(f"写入 DB 块失败: {e}")
            return False

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()
```

### 2. 数据解析工具类

```python
from dataclasses import dataclass
from enum import Enum

class DataType(Enum):
    """数据类型枚举"""
    INT = "INT"
    DINT = "DINT"
    REAL = "REAL"
    BOOL = "BOOL"
    BYTE = "BYTE"
    WORD = "WORD"
    DWORD = "DWORD"

@dataclass
class DBItem:
    """DB 块数据项定义"""
    name: str
    data_type: DataType
    start_offset: int
    bit_offset: int = 0  # 用于 BOOL 类型

class S7DataParser:
    """S7 数据解析器"""

    @staticmethod
    def parse_data(raw_data: bytes, item: DBItem):
        """
        解析原始数据为 Python 值

        Args:
            raw_data: 原始字节数据
            item: 数据项定义

        Returns:
            解析后的值
        """
        try:
            if item.data_type == DataType.INT:
                return get_int(raw_data, item.start_offset)
            elif item.data_type == DataType.DINT:
                return get_dint(raw_data, item.start_offset)
            elif item.data_type == DataType.REAL:
                return get_real(raw_data, item.start_offset)
            elif item.data_type == DataType.BOOL:
                return get_bool(raw_data, item.start_offset, item.bit_offset)
            elif item.data_type == DataType.BYTE:
                return get_byte(raw_data, item.start_offset)
            elif item.data_type == DataType.WORD:
                return get_word(raw_data, item.start_offset)
            elif item.data_type == DataType.DWORD:
                return get_dword(raw_data, item.start_offset)
            else:
                raise ValueError(f"不支持的数据类型: {item.data_type}")
        except Exception as e:
            logger.error(f"数据解析失败: {e}")
            return None
```

### 3. 实际应用示例

```python
# 示例：读取 PLC 实时数据
def read_plc_real_time():
    """读取 PLC 实时数据的示例"""

    # 定义要读取的数据项
    db_items = [
        DBItem("temperature", DataType.REAL, 0),      # DB1.DBD0
        DBItem("pressure", DataType.REAL, 4),         # DB1.DBD4
        DBItem("motor_speed", DataType.INT, 8),       # DB1.DBW8
        DBItem("motor_status", DataType.BOOL, 10, 0), # DB1.DBX10.0
        DBItem("alarm_count", DataType.DINT, 12),     # DB1.DBD12
    ]

    # 使用上下文管理器确保连接正确关闭
    with S7PLCConnector("192.168.0.1") as plc:
        if not plc.is_connected:
            return

        # 计算需要读取的总字节数
        max_offset = max(item.start_offset + item.data_type.value // 8
                        for item in db_items if item.data_type != DataType.BOOL) + 4

        # 读取整个数据块
        raw_data = plc.read_db(1, 0, max_offset)
        if not raw_data:
            return

        # 解析各个数据项
        parser = S7DataParser()
        results = {}

        for item in db_items:
            value = parser.parse_data(raw_data, item)
            results[item.name] = value
            logger.info(f"{item.name}: {value}")

        return results

# 示例：写入 PLC 数据
def write_plc_data():
    """写入 PLC 数据的示例"""

    with S7PLCConnector("192.168.0.1") as plc:
        if not plc.is_connected:
            return

        # 写入一个整数值 (例如：将电机速度设置为 1500)
        speed_data = set_int(1500)
        success = plc.write_db(1, 8, speed_data)

        if success:
            logger.info("成功写入电机速度值")
        else:
            logger.error("写入失败")
```

---

## 📊 高级功能实现

### 1. 数据监控类

```python
import threading
from datetime import datetime
import csv
import json

class S7DataMonitor:
    """PLC 数据实时监控器"""

    def __init__(self, plc_connector: S7PLCConnector, db_items: List[DBItem]):
        self.plc = plc_connector
        self.db_items = db_items
        self.is_monitoring = False
        self.monitor_thread = None
        self.data_history = []
        self.callbacks = []

    def add_callback(self, callback):
        """添加数据变化回调函数"""
        self.callbacks.append(callback)

    def start_monitoring(self, interval: float = 1.0):
        """开始监控数据"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info("开始监控 PLC 数据")

    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("停止监控 PLC 数据")

    def _monitor_loop(self, interval: float):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 读取数据
                data = self._read_all_data()
                if data:
                    # 添加时间戳
                    data['timestamp'] = datetime.now().isoformat()

                    # 保存历史记录
                    self.data_history.append(data)

                    # 限制历史记录数量
                    if len(self.data_history) > 10000:
                        self.data_history = self.data_history[-5000:]

                    # 调用回调函数
                    for callback in self.callbacks:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"回调函数执行失败: {e}")

                time.sleep(interval)

            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                time.sleep(interval)

    def _read_all_data(self) -> Optional[Dict]:
        """读取所有数据项"""
        # 计算读取范围
        max_offset = max(item.start_offset + 4 for item in self.db_items) + 4

        # 读取数据
        raw_data = self.plc.read_db(1, 0, max_offset)
        if not raw_data:
            return None

        # 解析数据
        parser = S7DataParser()
        results = {}

        for item in self.db_items:
            value = parser.parse_data(raw_data, item)
            results[item.name] = value

        return results

    def export_to_csv(self, filename: str):
        """导出历史数据到 CSV 文件"""
        if not self.data_history:
            logger.warning("没有历史数据可导出")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.data_history[0].keys())
            writer.writeheader()
            writer.writerows(self.data_history)

        logger.info(f"数据已导出到: {filename}")
```

### 2. 配置管理

```python
import yaml
from pathlib import Path

class S7Config:
    """S7 通信配置管理"""

    def __init__(self, config_file: str = "s7_config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            return self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        default_config = {
            'plc': {
                'ip_address': '192.168.0.1',
                'rack': 0,
                'slot': 1,
                'timeout': 10
            },
            'data_items': [
                {
                    'name': 'temperature',
                    'type': 'REAL',
                    'offset': 0
                },
                {
                    'name': 'pressure',
                    'type': 'REAL',
                    'offset': 4
                }
            ],
            'monitoring': {
                'interval': 1.0,
                'enable_logging': True
            }
        }

        # 保存默认配置
        self.save_config(default_config)
        return default_config

    def save_config(self, config=None):
        """保存配置到文件"""
        if config is None:
            config = self.config

        with open(self.config_file, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False,
                     allow_unicode=True, indent=2)

    def get_plc_config(self):
        """获取 PLC 配置"""
        return self.config.get('plc', {})

    def get_data_items(self) -> List[DBItem]:
        """获取数据项配置"""
        items = []
        for item_config in self.config.get('data_items', []):
            item = DBItem(
                name=item_config['name'],
                data_type=DataType(item_config['type']),
                start_offset=item_config['offset']
            )
            items.append(item)
        return items
```

---

## 🚀 完整应用示例

```python
# main.py - 主程序入口
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QPushButton
from PyQt6.QtCore import QTimer

class S7MonitorApp(QMainWindow):
    """S7 数据监控应用主窗口"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_s7_connection()

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("S7 PLC 数据监控")
        self.setGeometry(100, 100, 800, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建布局
        layout = QVBoxLayout(central_widget)

        # 创建数据表格
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["参数名称", "当前值"])
        layout.addWidget(self.table)

        # 创建控制按钮
        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self.start_monitoring)
        layout.addWidget(self.start_btn)

        # 创建定时器用于更新界面
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)

    def init_s7_connection(self):
        """初始化 S7 连接"""
        # 加载配置
        self.config = S7Config()

        # 创建 PLC 连接
        plc_config = self.config.get_plc_config()
        self.plc = S7PLCConnector(
            ip_address=plc_config['ip_address'],
            rack=plc_config['rack'],
            slot=plc_config['slot']
        )

        # 获取数据项
        self.data_items = self.config.get_data_items()

        # 设置表格行数
        self.table.setRowCount(len(self.data_items))

        # 填充参数名称
        for i, item in enumerate(self.data_items):
            self.table.setItem(i, 0, QTableWidgetItem(item.name))

        # 创建数据监控器
        self.monitor = S7DataMonitor(self.plc, self.data_items)
        self.monitor.add_callback(self.on_data_received)

    def start_monitoring(self):
        """开始监控"""
        if not self.plc.is_connected:
            if not self.plc.connect():
                self.show_error("连接 PLC 失败")
                return

        self.monitor.start_monitoring()
        self.timer.start(1000)  # 每秒更新一次界面
        self.start_btn.setText("停止监控")
        self.start_btn.clicked.disconnect()
        self.start_btn.clicked.connect(self.stop_monitoring)

    def stop_monitoring(self):
        """停止监控"""
        self.monitor.stop_monitoring()
        self.timer.stop()
        self.start_btn.setText("开始监控")
        self.start_btn.clicked.disconnect()
        self.start_btn.clicked.connect(self.start_monitoring)

    def on_data_received(self, data):
        """接收到数据时的回调"""
        self.current_data = data

    def update_display(self):
        """更新界面显示"""
        if hasattr(self, 'current_data'):
            for i, item in enumerate(self.data_items):
                value = self.current_data.get(item.name)
                if value is not None:
                    self.table.setItem(i, 1, QTableWidgetItem(str(value)))

    def show_error(self, message):
        """显示错误信息"""
        print(f"错误: {message}")  # 实际应用中应使用消息框

    def closeEvent(self, event):
        """窗口关闭事件"""
        self.monitor.stop_monitoring()
        self.plc.disconnect()
        event.accept()

# 程序入口
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = S7MonitorApp()
    window.show()
    sys.exit(app.exec())
```

---

## 🐛 常见问题与解决方案

### 1. 连接问题

**问题**: 连接 PLC 时超时
```python
# 解决方案：增加连接超时时间
client = snap7.client.Client()
client.set_param(snap7.snap7types.S7Param.PingTimeout, 5000)  # 5秒超时
```

**问题**: 连接被拒绝
- 检查 PLC 是否勾选了 "允许 PUT/GET 通信"
- 确认 IP 地址、机架号、槽位号正确
- 检查网络防火墙设置

### 2. 数据读取问题

**问题**: 读取数据全为 0
```python
# 解决方案：检查 DB 块是否为优化块
# 非优化块才能使用地址访问，优化块需要符号访问
```

**问题**: 数据类型转换错误
```python
# 解决方案：确保数据类型匹配
# 例如：REAL 类型占 4 字节，INT 类型占 2 字节
```

### 3. 性能优化

**批量读取优化**:
```python
# 优化前：多次读取
for item in items:
    data = plc.read_db(1, item.offset, item.size)

# 优化后：一次读取所有数据
total_size = max(item.offset + item.size for item in items)
raw_data = plc.read_db(1, 0, total_size)
```

**异步读取优化**:
```python
import asyncio

async def read_async(plc, db_number, offset, size):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, plc.read_db, db_number, offset, size)
```

---

## 📚 进阶主题

### 1. 错误处理和重连机制

```python
class S7ReconnectingConnector(S7PLCConnector):
    """带重连功能的 S7 连接器"""

    def __init__(self, ip_address: str, max_retries: int = 3, retry_interval: float = 5.0):
        super().__init__(ip_address)
        self.max_retries = max_retries
        self.retry_interval = retry_interval

    def connect_with_retry(self) -> bool:
        """带重试的连接"""
        for attempt in range(self.max_retries):
            try:
                if self.connect():
                    return True
            except Exception as e:
                logger.error(f"连接尝试 {attempt + 1} 失败: {e}")

            if attempt < self.max_retries - 1:
                time.sleep(self.retry_interval)

        return False

    def read_with_reconnect(self, db_number: int, start_offset: int, size: int):
        """带重连的读取"""
        for attempt in range(self.max_retries):
            try:
                data = self.read_db(db_number, start_offset, size)
                if data is not None:
                    return data
            except Exception as e:
                logger.error(f"读取尝试 {attempt + 1} 失败: {e}")

                # 尝试重新连接
                self.disconnect()
                if self.connect_with_retry():
                    continue

        return None
```

### 2. 数据缓存机制

```python
from collections import deque
import time

class S7DataCache:
    """S7 数据缓存管理器"""

    def __init__(self, ttl: float = 1.0):
        self.cache = {}
        self.ttl = ttl
        self.timestamps = {}

    def get(self, key: str):
        """获取缓存数据"""
        if key in self.cache:
            age = time.time() - self.timestamps[key]
            if age < self.ttl:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value):
        """设置缓存数据"""
        self.cache[key] = value
        self.timestamps[key] = time.time()

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.timestamps.clear()
```

### 3. 多 PLC 管理

```python
class S7PLCManager:
    """多 PLC 管理器"""

    def __init__(self):
        self.plcs = {}

    def add_plc(self, name: str, ip_address: str, rack: int = 0, slot: int = 1):
        """添加 PLC"""
        self.plcs[name] = S7PLCConnector(ip_address, rack, slot)

    def connect_all(self):
        """连接所有 PLC"""
        results = {}
        for name, plc in self.plcs.items():
            results[name] = plc.connect()
        return results

    def read_all(self, db_number: int, start_offset: int, size: int):
        """从所有 PLC 读取数据"""
        results = {}
        for name, plc in self.plcs.items():
            results[name] = plc.read_db(db_number, start_offset, size)
        return results

    def disconnect_all(self):
        """断开所有 PLC 连接"""
        for plc in self.plcs.values():
            plc.disconnect()
```

---

## 🎯 最佳实践

### 1. 代码组织
- 使用面向对象封装功能
- 将配置与代码分离
- 实现清晰的错误处理
- 添加详细的日志记录

### 2. 性能优化
- 批量读取而非单个读取
- 使用数据缓存减少通信
- 异步处理提高响应速度
- 合理设置读取频率

### 3. 安全考虑
- 验证输入参数范围
- 处理网络异常情况
- 实现访问控制机制
- 加密敏感配置信息

### 4. 可维护性
- 编写单元测试
- 使用版本控制
- 文档完善
- 代码注释清晰

---

## 📝 总结

本文档提供了完整的 Python S7 通信开发指南，包括：

1. **环境搭建** - Python 3.11.13 环境和依赖安装
2. **基础实现** - 核心连接和读写功能
3. **高级功能** - 实时监控、数据缓存、多PLC管理
4. **最佳实践** - 代码组织、性能优化、安全考虑

通过本文档，您可以快速搭建一个稳定、高效的 PLC 数据采集系统。

---

## 🔗 参考资源

- [Snap7 官方文档](https://github.com/snap7/snap7)
- [Python-snap7 文档](https://python-snap7.readthedocs.io/)
- [西门子 S7 通信协议](https://support.industry.siemens.com/)
- [TIA Portal 编程指南](https://support.industry.siemens.com/)

---

*最后更新时间: 2024-12-20*
*版本: 1.0*