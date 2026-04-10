#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Snap7 客户端属性
"""

import snap7

def check_snap7_attributes():
    """检查 Snap7 客户端的所有属性"""

    print("=" * 60)
    print("Snap7 客户端属性检查")
    print("=" * 60)

    # 创建客户端
    client = snap7.client.Client()

    print("Snap7 客户端的所有属性和方法：")
    print("-" * 60)

    # 获取所有属性和方法
    all_attrs = dir(client)

    # 筛选可能的连接状态属性
    connection_attrs = [attr for attr in all_attrs if 'connect' in attr.lower()]

    print("包含 'connect' 的属性：")
    for attr in connection_attrs:
        print(f"  - {attr}")

    print("\n所有属性（前20个）：")
    for i, attr in enumerate(all_attrs[:20]):
        print(f"  {i+1:2d}. {attr}")

    print(f"\n总共有 {len(all_attrs)} 个属性和方法")

    # 检查特定的连接相关属性
    test_attrs = ['connected', 'Connected', 'is_connected', 'IsConnected', 'connection', 'Connection']

    print("\n检查连接状态相关属性：")
    for attr in test_attrs:
        if hasattr(client, attr):
            value = getattr(client, attr)
            print(f"  ✅ {attr} = {value}")
        else:
            print(f"  ❌ {attr} 不存在")

    # 尝试连接并检查状态
    print("\n" + "-" * 60)
    print("尝试连接 PLC...")

    try:
        client.connect('192.168.0.1', 0, 1)
        print("连接命令执行成功")

        # 再次检查连接状态
        print("\n连接后的状态检查：")
        for attr in test_attrs:
            if hasattr(client, attr):
                try:
                    value = getattr(client, attr)
                    print(f"  ✅ {attr} = {value} (类型: {type(value)})")
                except Exception as e:
                    print(f"  ❌ {attr} 访问失败: {e}")

        # 检查一些可能的状态方法
        status_methods = ['get_connected', 'is_connected', 'check_connection', 'ConnectionTime']
        print("\n检查连接状态方法：")
        for method in status_methods:
            if hasattr(client, method):
                try:
                    if callable(getattr(client, method)):
                        result = getattr(client, method)()
                        print(f"  ✅ {method}() = {result}")
                    else:
                        value = getattr(client, method)
                        print(f"  ✅ {method} = {value}")
                except Exception as e:
                    print(f"  ❌ {method} 调用失败: {e}")

    except Exception as e:
        print(f"连接失败: {e}")
    finally:
        try:
            client.disconnect()
            print("\n连接已断开")
        except:
            pass

if __name__ == "__main__":
    check_snap7_attributes()