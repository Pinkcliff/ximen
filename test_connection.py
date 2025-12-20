#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接测试脚本 - 用于调试 PLC 连接问题
"""

import snap7
from datetime import datetime

def test_plc_connection(ip_address="192.168.0.1", rack=0, slot=1):
    """测试 PLC 连接"""

    print("=" * 60)
    print("PLC 连接测试")
    print("=" * 60)
    print(f"目标 IP: {ip_address}")
    print(f"机架号: {rack}")
    print(f"槽位号: {slot}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    client = snap7.client.Client()

    try:
        # 1. 测试网络连通性
        print("1. 测试网络连通性...")
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip_address, 102))  # S7 协议默认端口
        sock.close()

        if result == 0:
            print("✅ 网络连接正常 (端口 102 可达)")
        else:
            print(f"❌ 网络连接失败 (端口 102 不可达，错误代码: {result})")
            print("   请检查：")
            print("   - PLC IP 地址是否正确")
            print("   - 网络连接是否正常")
            print("   - 防火墙是否阻止连接")
            return False

        # 2. 尝试连接 PLC
        print("\n2. 尝试连接 PLC...")
        try:
            client.connect(ip_address, rack, slot)
            print("✅ PLC 连接成功")
        except Exception as e:
            print(f"❌ PLC 连接失败: {e}")
            return False

        # 3. 检查连接状态
        print("\n3. 检查连接状态...")
        if client.get_connected():
            print("✅ 连接状态: 已连接")
        else:
            print(f"❌ 连接状态: {client.get_connected()}")
            return False

        # 4. 读取 PLC 信息
        print("\n4. 读取 PLC 信息...")
        try:
            # 获取 CPU 状态
            status = client.get_cpu_state()
            print(f"   CPU 状态: {status}")

            # 获取 PLC 订单号
            try:
                order_number = client.GetOrderNumber()
                print(f"   PLC 型号: {order_number}")
            except:
                print(f"   PLC 型号: 无法获取")

            # 获取模块类型
            try:
                module_type = client.GetModuleType()
                print(f"   模块类型: {module_type}")
            except:
                print(f"   模块类型: 无法获取")

        except Exception as e:
            print(f"❌ 读取 PLC 信息失败: {e}")

        # 5. 测试读取数据
        print("\n5. 测试读取 DB5 数据...")
        try:
            # 读取 DB5 的前几个字节
            data = client.db_read(5, 0, 10)
            print(f"   DB5 前 10 字节: {data.hex()}")

            # 尝试读取偏移量 124 处的数据 (右缸编码器位置)
            encoder_data = client.db_read(5, 124, 4)
            print(f"   DB5.DBD124 (右缸编码器): {encoder_data.hex()}")

            # 转换为 Real 值
            from snap7.util import get_real
            position = get_real(encoder_data, 0)
            print(f"   转换后位置值: {position:.3f} mm")

        except Exception as e:
            print(f"❌ 读取 DB5 数据失败: {e}")
            print("   可能原因：")
            print("   - DB5 数据块不存在")
            print("   - DB5 未启用 PUT/GET 访问")
            print("   - 数据块类型为优化块")

        return True

    except Exception as e:
        print(f"❌ 连接过程异常: {e}")
        return False
    finally:
        try:
            if client.get_connected():
                client.disconnect()
                print("\n✅ 连接已断开")
        except:
            pass

def check_s7_common_errors():
    """检查常见的 S7 连接问题"""
    print("\n" + "=" * 60)
    print("常见问题检查清单")
    print("=" * 60)
    print("✅ 需要确认的 PLC 设置：")
    print("   1. TIA Portal 中勾选了 '允许来自远程对象的PUT/GET通信访问'")
    print("   2. DB5 数据块存在并且不是优化块")
    print("   3. PLC 与上位机在同一网段")
    print("   4. 防火墙允许端口 102 的通信")
    print("   5. PLC IP 地址正确无误")
    print("\n📝 如何在 TIA Portal 中设置：")
    print("   1. 打开 TIA Portal 项目")
    print("   2. 进入 '设备组态'")
    print("   3. 选择 CPU 的以太网接口")
    print("   4. 在 '属性' → '连接机制' 中勾选相应选项")

if __name__ == "__main__":
    # 测试连接
    success = test_plc_connection()

    # 显示问题检查清单
    check_s7_common_errors()

    print("\n" + "=" * 60)
    if success:
        print("🎉 连接测试成功！可以尝试读取编码器位置数据了。")
    else:
        print("❌ 连接测试失败，请根据上述提示检查相关设置。")
    print("=" * 60)