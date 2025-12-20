#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
右缸编码器反馈位置读取程序
读取 DB5 Static 中最后一个 Real 类型的编码器反馈位置数据
"""

import sys
import time
from datetime import datetime
from loguru import logger
import snap7
from snap7.util import get_real

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
    level="INFO"
)
logger.add(
    "encoder_position.log",
    rotation="10 MB",
    retention="7 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    level="DEBUG"
)

class EncoderPositionReader:
    """编码器位置读取器"""

    def __init__(self, plc_ip="192.168.0.1", rack=0, slot=1):
        """
        初始化编码器位置读取器

        Args:
            plc_ip: PLC IP地址
            rack: 机架号 (默认0)
            slot: 槽位号 (默认1)
        """
        self.plc_ip = plc_ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.is_connected = False

        # DB5 配置 - 根据图片信息更新
        # 右缸编码器反馈位置在 DB5 偏移量 124.0 处
        self.db_number = 5
        self.encoder_offset = 124  # 根据图片信息，偏移量为124
        self.data_size = 4  # Real 类型占用 4 字节

        logger.info(f"编码器位置读取器初始化完成")
        logger.info(f"PLC IP: {self.plc_ip}")
        logger.info(f"读取地址: DB{self.db_number}.DBD{self.encoder_offset}")
        logger.info(f"数据类型: Real (4 字节)")

    def connect(self) -> bool:
        """连接到 PLC"""
        try:
            logger.info(f"正在连接 PLC: {self.plc_ip}")
            self.client.connect(self.plc_ip, self.rack, self.slot)

            # 检查连接状态
            if self.client.get_connected():
                self.is_connected = True
                logger.success("PLC 连接成功")
                return True
            else:
                error_msg = f"PLC 连接失败，连接状态: {self.client.get_connected()}"
                logger.error(error_msg)
                # 获取详细错误信息
                error_text = self.client.ErrorText()
                logger.error(f"错误信息: {error_text}")
                return False

        except Exception as e:
            logger.error(f"连接异常: {e}")
            return False

    def disconnect(self):
        """断开 PLC 连接"""
        if self.is_connected and self.client.get_connected():
            try:
                self.client.disconnect()
                self.is_connected = False
                logger.info("PLC 连接已断开")
            except Exception as e:
                logger.error(f"断开连接异常: {e}")

    def read_encoder_position(self) -> float:
        """
        读取右缸编码器反馈位置

        Returns:
            float: 编码器位置值，失败返回 None
        """
        if not self.is_connected:
            logger.error("PLC 未连接")
            return None

        try:
            # 读取 DB5 中的编码器位置数据
            logger.debug(f"读取 DB{self.db_number}.DBD{self.encoder_offset}")
            data = self.client.db_read(self.db_number, self.encoder_offset, self.data_size)

            if len(data) == self.data_size:
                # 将字节数据转换为 Real 类型
                position = get_real(data, 0)
                logger.debug(f"原始数据: {data.hex()}")
                logger.info(f"右缸编码器反馈位置: {position} mm")
                return position
            else:
                logger.error(f"读取数据长度不正确: 期望 {self.data_size} 字节, 实际 {len(data)} 字节")
                return None

        except Exception as e:
            logger.error(f"读取编码器位置失败: {e}")
            return None

    def read_position_with_retry(self, max_retries=3, retry_delay=1.0) -> float:
        """
        带重试机制的读取

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟时间(秒)

        Returns:
            float: 编码器位置值
        """
        for attempt in range(max_retries):
            try:
                position = self.read_encoder_position()
                if position is not None:
                    return position

            except Exception as e:
                logger.error(f"第 {attempt + 1} 次读取失败: {e}")

            if attempt < max_retries - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)

        logger.error("所有重试均失败")
        return None

    def continuous_monitoring(self, interval=1.0, duration=None):
        """
        连续监控编码器位置

        Args:
            interval: 读取间隔时间(秒)
            duration: 监控持续时间(秒), None 表示无限监控
        """
        logger.info(f"开始连续监控，间隔: {interval} 秒")

        start_time = time.time()
        read_count = 0
        success_count = 0

        try:
            while True:
                current_time = time.time()

                # 检查监控时间
                if duration and (current_time - start_time) >= duration:
                    logger.info("监控时间结束")
                    break

                # 读取位置
                position = self.read_encoder_position()
                read_count += 1

                if position is not None:
                    success_count += 1
                    # 在这里可以添加数据处理逻辑，如保存到文件、发送到其他系统等
                    # self.save_position_to_file(position, datetime.now())
                else:
                    logger.warning("读取失败")

                # 等待下一次读取
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("用户中断监控")
        except Exception as e:
            logger.error(f"监控过程异常: {e}")
        finally:
            success_rate = (success_count / read_count * 100) if read_count > 0 else 0
            logger.info(f"监控结束，总读取次数: {read_count}, 成功次数: {success_count}, 成功率: {success_rate:.1f}%")

    def save_position_to_file(self, position: float, timestamp: datetime, filename="encoder_data.txt"):
        """
        保存位置数据到文件

        Args:
            position: 位置值
            timestamp: 时间戳
            filename: 文件名
        """
        try:
            with open(filename, "a", encoding="utf-8") as f:
                f.write(f"{timestamp.isoformat()},{position:.3f}\n")
            logger.debug(f"数据已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存文件失败: {e}")

    def validate_position_range(self, position: float, min_val=-1000.0, max_val=1000.0) -> bool:
        """
        验证位置值是否在合理范围内

        Args:
            position: 位置值
            min_val: 最小值
            max_val: 最大值

        Returns:
            bool: 是否在合理范围内
        """
        if position is None:
            return False

        if min_val <= position <= max_val:
            return True
        else:
            logger.warning(f"位置值超出合理范围: {position} (期望: {min_val} ~ {max_val})")
            return False

    def get_plc_info(self):
        """获取 PLC 信息"""
        if not self.is_connected:
            logger.error("PLC 未连接")
            return None

        try:
            # 获取 PLC 系统状态
            status = self.client.get_cpu_state()
            logger.info(f"PLC 状态: {status}")

            # 获取 PLC 订单号
            order_number = self.client.get_order_number()
            logger.info(f"PLC 订单号: {order_number}")

            return {
                "status": status,
                "order_number": order_number
            }
        except Exception as e:
            logger.error(f"获取 PLC 信息失败: {e}")
            return None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


def main():
    """主函数 - 演示各种读取模式"""

    print("=" * 60)
    print("右缸编码器反馈位置读取程序")
    print("=" * 60)

    # 使用上下文管理器确保连接正确关闭
    with EncoderPositionReader(plc_ip="192.168.0.1") as reader:

        # 1. 检查连接状态
        if not reader.is_connected:
            logger.error("无法连接到 PLC，程序退出")
            return

        # 2. 获取 PLC 信息
        logger.info("\n--- PLC 信息 ---")
        plc_info = reader.get_plc_info()

        # 3. 单次读取
        logger.info("\n--- 单次读取测试 ---")
        position = reader.read_position_with_retry(max_retries=3)
        if position is not None:
            logger.success(f"读取成功: 右缸编码器位置 = {position:.3f} mm")

            # 验证数据合理性
            if reader.validate_position_range(position, -500, 500):
                logger.info("位置值在合理范围内")
            else:
                logger.warning("位置值可能异常")
        else:
            logger.error("读取失败")
            return

        # 4. 连续监控演示
        logger.info("\n--- 连续监控演示 (10秒) ---")
        logger.info("按 Ctrl+C 可提前退出监控")
        try:
            reader.continuous_monitoring(interval=0.5, duration=10)
        except KeyboardInterrupt:
            logger.info("用户取消监控")

        logger.success("\n程序执行完成")


def test_configuration():
    """测试配置 - 用于调试"""
    print("配置测试模式")
    print("-" * 30)

    # 测试不同的偏移地址
    test_offsets = [16, 20, 24, 28, 32]  # 根据实际 DB 结构调整

    with EncoderPositionReader(plc_ip="192.168.0.1") as reader:
        if not reader.is_connected:
            print("连接失败")
            return

        for offset in test_offsets:
            reader.encoder_offset = offset
            print(f"\n测试偏移地址 {offset}:")

            data = reader.client.db_read(reader.db_number, offset, 4)
            print(f"原始数据: {data.hex()}")

            try:
                value = get_real(data, 0)
                print(f"Real 值: {value}")
            except:
                print("无法解析为 Real 类型")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="右缸编码器反馈位置读取程序")
    parser.add_argument("--test", action="store_true", help="运行配置测试模式")
    parser.add_argument("--monitor", type=int, metavar="SECONDS",
                       help="连续监控模式，指定监控时间（秒）")
    parser.add_argument("--ip", default="192.168.0.1",
                       help="PLC IP 地址 (默认: 192.168.0.1)")
    parser.add_argument("--offset", type=int, default=20,
                       help="编码器数据偏移地址 (默认: 20)")

    args = parser.parse_args()

    if args.test:
        test_configuration()
    elif args.monitor:
        with EncoderPositionReader(plc_ip=args.ip) as reader:
            reader.encoder_offset = args.offset
            print(f"\n开始监控 DB{reader.db_number}.DBD{args.offset}")
            reader.continuous_monitoring(interval=1.0, duration=args.monitor)
    else:
        main()