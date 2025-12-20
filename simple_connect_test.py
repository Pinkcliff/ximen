#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的 PLC 通信测试脚本
专门用于测试是否能与 PLC 建立连接
"""

import snap7
import time

def test_plc_connect():
    """测试 PLC 连接"""

    print("=" * 50)
    print("PLC 通信测试")
    print("=" * 50)

    # 创建 S7 客户端
    client = snap7.client.Client()

    try:
        # 1. 显示客户端信息
        print(f"Snap7 客户端创建成功")
        print(f"客户端版本: {client.get_cp_info()}")

        # 2. 尝试连接 PLC
        print(f"\n正在连接 PLC: 192.168.0.1")
        print(f"机架号: 0, 槽位号: 1")

        # 尝试连接
        client.connect('192.168.0.1', 0, 1)

        # 3. 检查连接状态
        print(f"\n连接状态: {client.Connected}")

        if client.Connected == 1:
            print("✅ PLC 连接成功！")

            # 4. 尝试读取一些基本信息
            print(f"\n正在读取 PLC 信息...")

            try:
                # 读取 CPU 状态
                status = client.get_cpu_state()
                print(f"CPU 状态: {status}")

                # 读取系统状态
                system_status = client.get_system_status_list()
                print(f"系统状态: {system_status}")

                # 读取 PLC 时间
                plc_time = client.get_plc_datetime()
                print(f"PLC 时间: {plc_time}")

                return True

            except Exception as e:
                print(f"读取 PLC 信息时出错: {e}")
                return True  # 连接成功，但读取失败

        else:
            print("❌ PLC 连接失败！")
            return False

    except Exception as e:
        print(f"❌ 连接过程出错: {e}")
        print(f"错误类型: {type(e).__name__}")

        # 尝试获取更详细的错误信息
        try:
            error_text = client.ErrorText()
            print(f"Snap7 错误信息: {error_text}")
        except:
            pass

        return False

    finally:
        # 断开连接
        try:
            if client.Connected == 1:
                client.disconnect()
                print("\n连接已断开")
        except:
            pass

def test_network_ping():
    """测试网络连通性"""
    import socket

    print("\n" + "-" * 50)
    print("网络连通性测试")
    print("-" * 50)

    # 测试 ping
    try:
        # 尝试连接 S7 端口 (102)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)

        result = sock.connect_ex(('192.168.0.1', 102))

        if result == 0:
            print("✅ 网络连接正常 (端口 102 可达)")
            return True
        else:
            print(f"❌ 网络连接失败 (端口 102 不可达)")
            print(f"   错误代码: {result}")

            # 尝试 ping 测试
            print("\n尝试 ping 测试...")
            try:
                import subprocess
                ping_result = subprocess.run(
                    ['ping', '-n', '1', '192.168.0.1'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if ping_result.returncode == 0:
                    print("✅ Ping 成功")
                    print("   问题可能是：PLC 未启用 S7 服务或端口被阻止")
                else:
                    print("❌ Ping 失败")
                    print("   问题可能是：IP 地址错误或网络不通")
            except:
                print("无法执行 ping 测试")

            return False

    except Exception as e:
        print(f"网络测试异常: {e}")
        return False

    finally:
        sock.close()

if __name__ == "__main__":
    print(f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 先测试网络连通性
    network_ok = test_network_ping()

    # 再测试 PLC 连接
    if network_ok:
        print("\n")
        plc_ok = test_plc_connect()

        if plc_ok:
            print("\n🎉 通信测试成功！")
            print("现在可以尝试读取 DB5 数据了")
        else:
            print("\n❌ PLC 连接失败")
            print("请检查 PLC 设置和网络配置")
    else:
        print("\n❌ 网络连通性测试失败")
        print("请先解决网络连接问题")

    print(f"\n结束时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")