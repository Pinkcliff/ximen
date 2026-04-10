#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速读取右缸编码器位置 - 简化版
"""

import snap7
from snap7.util import get_real
import yaml
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

def load_config():
    """加载配置文件"""
    config_file = PROJECT_ROOT / "config" / "encoder_config.yaml"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # 默认配置
        return {
            'plc': {
                'ip_address': '192.168.0.1',
                'rack': 0,
                'slot': 1
            },
            'data': {
                'db_number': 5,
                'offset': 124,  # 根据图片信息，偏移量为124
                'data_size': 4
            }
        }

def read_encoder_position():
    """读取右缸编码器位置"""

    # 加载配置
    config = load_config()
    plc_config = config['plc']
    data_config = config['data']

    print(f"连接 PLC: {plc_config['ip_address']}")
    print(f"读取地址: DB{data_config['db_number']}.DBD{data_config['offset']}")

    # 创建客户端
    client = snap7.client.Client()

    try:
        # 连接 PLC
        client.connect(
            plc_config['ip_address'],
            plc_config['rack'],
            plc_config['slot']
        )

        # 检查连接状态
        if client.get_connected():
            print("✅ PLC 连接成功")

            # 读取数据
            data = client.db_read(
                data_config['db_number'],
                data_config['offset'],
                data_config['data_size']
            )

            print(f"原始数据: {data.hex()}")

            # 转换为 Real 值
            position = get_real(data, 0)
            print(f"🎯 右缸编码器反馈位置: {position:.3f} mm")

            return position

        else:
            print(f"❌ PLC 连接失败，连接状态: {client.get_connected()}")
            # 获取详细错误信息
            error_code = client.ErrorText()
            print(f"❌ 错误信息: {error_code}")
            return None

    except Exception as e:
        print(f"❌ 读取异常: {e}")
        return None
    finally:
        client.disconnect()

if __name__ == "__main__":
    print("=" * 50)
    print("右缸编码器位置快速读取")
    print("=" * 50)

    position = read_encoder_position()

    if position is not None:
        print("\n✅ 读取成功！")
    else:
        print("\n❌ 读取失败！")
        print("\n请检查：")
        print("1. PLC IP 地址是否正确")
        print("2. PLC 是否启用 PUT/GET 通信")
        print("3. DB5 偏移地址是否正确")
        print("4. 网络连接是否正常")