已为您创建了完整的右缸编码器反馈位置读取程序！

  📁 创建的文件

  1. read_encoder_position.py - 主程序

  - 完整的编码器位置读取功能
  - 支持单次读取和连续监控
  - 包含错误处理和重试机制
  - 详细的日志记录功能

  2. quick_read_encoder.py - 快速版本

  - 简化的快速读取程序
  - 适合快速测试和调试
  - 支持配置文件

  3. encoder_config.yaml - 配置文件

  - 管理所有连接参数
  - 可调整 DB5 偏移地址
  - 包含调试和测试配置

  4. install_requirements.bat - 安装脚本

  - 自动安装所有依赖库
  - 检查 Python 环境
  - 提供使用说明

  🚀 使用步骤

  1. 安装依赖

  # 方法1：使用批处理文件（Windows）
  install_requirements.bat

  # 方法2：手动安装
  pip install python-snap7 pyyaml loguru

  2. 配置参数

  编辑 encoder_config.yaml 文件，修改以下参数：
  plc:
    ip_address: "192.168.0.1"  # 修改为实际 PLC IP

  data:
    offset: 20  # 修改为实际的 DB5 偏移地址

  3. 运行程序

  # 快速读取
  python quick_read_encoder.py

  # 完整功能
  python read_encoder_position.py

  # 连续监控 30 秒
  python read_encoder_position.py --monitor 30

  # 测试不同偏移地址
  python read_encoder_position.py --test

  ⚠️ 重要提醒

  1. 确认偏移地址：您需要确认 DB5.Static 中最后一个 Real 类型的实际偏移地 
址
  2. PLC 设置：确保 PLC 已启用 PUT/GET 通信访问
  3. 数据块类型：确认 DB5 是非优化的数据块
  4. 网络连通性：确保上位机与 PLC 网络连通

  如需要调整任何参数或遇到问题，请告诉我！