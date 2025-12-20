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


  现在请运行这两个脚本：

  1. 首先检查 Snap7 属性：
  python check_snap7_attrs.py

  2. 然后尝试简单读取：
  python simple_read_test.py

  第一个脚本会告诉我们 Snap7 库到底有哪些可用的属性，这样我们就能知道正确的连接状态 
检查方法是什么。

  第二个脚本会直接尝试读取数据，不依赖连接状态检查，这样可能能直接读取到编码器位置数
据。

  请运行这两个脚本并告诉我结果！

   现在您可以测试了！

  请在您的测试电脑上运行以下任一脚本：

  # 1. 快速读取测试
  python quick_read_encoder.py

  # 2. 连接测试
  python test_connection.py

  # 3. 简单读取测试
  python simple_read_test.py

  🎉 GUI 实时监控程序已创建完成！

  我为您创建了两个版本的图形界面程序：

  📁 创建的文件：

  1. encoder_monitor_gui.py - 完整版 GUI（功能更丰富）
  2. simple_encoder_gui.py - 简化版 GUI（依赖更少）
  3. install_gui_dependencies.bat - GUI 依赖安装脚本

  🎯 程序功能特点：

  完整版功能：

  - ✅ 实时位置显示 - 大号 LCD 数字显示
  - ✅ 实时曲线图 - 使用 pyqtgraph 绘制专业图表
  - ✅ 位置变化检测 - 可调节阈值，实时提醒
  - ✅ 统计信息 - 最大值、最小值、平均值、变化次数
  - ✅ 详细日志 - 记录所有位置变化
  - ✅ 可调节读取频率 - 滑块调节更新速度
  - ✅ 暗色主题 - 护眼的现代界面

  简化版功能：

  - ✅ 实时位置显示 - 清晰的数字显示
  - ✅ 实时曲线图 - 自定义绘图组件
  - ✅ 位置变化检测 - 自动检测并提醒
  - ✅ 基本统计信息 - 最大值、最小值、变化次数
  - ✅ 日志记录 - 记录重要事件
  - ✅ 更少依赖 - 只需要 PyQt6

  🚀 使用方法：

  1. 安装依赖

  # 完整版（需要 pyqtgraph）
  install_gui_dependencies.bat

  # 或者手动安装
  pip install python-snap7 PyQt6 pyqtgraph numpy

  2. 运行程序

  推荐使用简化版（依赖更少）：
  python simple_encoder_gui.py

  或者使用完整版：
  python encoder_monitor_gui.py

  💡 使用说明：

  1. 启动程序 - 运行上述命令
  2. 点击"开始监控" - 开始实时读取数据
  3. 观察位置变化 - 当位置发生变化时会：
    - 实时更新数字显示
    - 在曲线上显示变化
    - 变化指示器变绿色
    - 记录到日志
  4. 调整设置：
    - 变化阈值：设置多少算作"变化"
    - 读取频率：调整更新速度
    - 清除数据：重新开始统计

  现在您可以实时监控右缸编码器位置的变化了！当位置发生变化时，程序会立即通知您！  