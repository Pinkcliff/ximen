# 西门子 S7 PLC 编码器监控项目

基于 Python 的西门子 PLC S7 协议通信项目，用于读取和监控编码器位置数据。

## 📁 项目结构

```
ximen/
├── src/                    # 源代码
│   ├── encoders/          # 编码器相关程序
│   ├── point_table/       # 点位表监控程序
│   └── utils/             # 工具和测试脚本
├── config/                # 配置文件
├── scripts/               # 安装脚本
├── docs/                  # 文档
├── data/                  # 数据文件
└── backup/                # 备份文件夹
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# Windows
scripts\install_requirements.bat
```

### 2. 运行程序

**点位表可视化监控（推荐）**：
```bash
python src/point_table/point_table_monitor_gui.py
```

**编码器位置读取**：
```bash
python src/encoders/read_encoder_position.py
```

## 📚 文档

详细使用说明请查看 [docs/README.md](docs/README.md)

## 🔧 配置

- **编码器配置**: `config/encoder_config.yaml`
- **点位表配置**: `config/batch_config.yaml`
- **点位表数据**: `data/点位表.xlsx`

## 📝 主要功能

- ✅ S7 协议 PLC 通信
- ✅ 编码器位置实时读取
- ✅ 点位表批量数据监控
- ✅ 可视化 GUI 界面
- ✅ 支持多种数据类型（REAL, BOOL, INT, DINT）

## 🛠️ 技术栈

- Python 3.11+
- python-snap7 (S7 通信)
- PyQt6 (GUI 界面)
- pandas (数据处理)
- openpyxl (Excel 读取)
