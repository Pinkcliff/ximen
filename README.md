# PLC点位表可视化监控

## 📊 功能介绍

可视化监控程序，实时显示PLC所有点位数据。

### 界面功能

- ✅ **控制面板** - 连接/断开PLC、开始/停止监控
- ✅ **数据表格** - 显示所有点位的详细信息
- ✅ **实时刷新** - 1秒间隔自动更新
- ✅ **统计信息** - 显示总点数、成功/失败数量
- ✅ **状态指示** - BOOL类型用颜色表示True/False
- ✅ **暗色主题** - 护眼的现代化界面

### 支持的数据类型

- REAL - 浮点数（蓝色背景）
- BOOL - 布尔值（绿色=True，灰色=False）
- INT/DINT - 整数
- WORD/DWORD - 字数据

## 🚀 使用方法

### 1. 安装依赖

```bash
# Windows
install_gui_monitor.bat

# 或手动安装
pip install python-snap7 PyQt6 pandas openpyxl loguru pyyaml
```

### 2. 修改PLC配置

编辑 `point_table_monitor_gui.py`，修改PLC IP地址：

```python
self.client.connect("192.168.0.1", 0, 1)  # 修改为实际IP
```

### 3. 运行程序

```bash
python point_table_monitor_gui.py
```

### 4. 操作说明

1. 点击 **"连接PLC"** - 连接到PLC
2. 点击 **"开始监控"** - 开始实时刷新数据
3. 点击 **"单次刷新"** - 手动刷新一次数据
4. 点击 **"清除数据"** - 清除表格显示

## 📁 相关文件

- `point_table_monitor_gui.py` - GUI监控程序
- `batch_read_points.py` - 批量读取命令行程序
- `点位表.xlsx` - 点位表数据
- `batch_config.yaml` - 配置文件

## 🔧 点位表格式

点位表Excel文件格式：

| 名称 | 地址 | 数据类型 |
|------|------|----------|
| 台板速度反馈 | DB6.12.0 | REAL |
| 台板使能接通 | DB5.0.0 | BOOL |

地址格式：`DB块号.字节偏移.位偏移`

例如：`DB5.128.0` 表示 DB5 数据块，偏移 128 字节，第 0 位
