#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单读取测试 - 不检查连接状态，直接尝试读取
"""

import snap7
from snap7.util import get_real

def simple_read_test():
    """简单读取测试"""

    print("=" * 50)
    print("简单读取测试")
    print("=" * 50)

    # 创建客户端
    client = snap7.client.Client()

    try:
        print("正在连接 PLC: 192.168.0.1")

        # 直接连接，不检查状态
        client.connect('192.168.0.1', 0, 1)
        print("✅ PLC 连接成功")

        # 直接尝试读取数据
        print("\n正在读取 DB5.DBD124...")
        data = client.db_read(5, 124, 4)

        print(f"✅ 读取成功")
        print(f"原始数据: {data.hex()}")

        # 转换为 Real 值
        position = get_real(data, 0)
        print(f"🎯 右缸编码器位置: {position:.3f} mm")

        return position

    except Exception as e:
        print(f"❌ 读取失败: {e}")
        print(f"错误类型: {type(e).__name__}")
        return None

    finally:
        try:
            client.disconnect()
            print("\n连接已断开")
        except:
            pass

if __name__ == "__main__":
    position = simple_read_test()

    if position is not None:
        print("\n🎉 读取成功！")
    else:
        print("\n❌ 读取失败！")