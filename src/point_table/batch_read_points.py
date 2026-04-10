#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
根据点位表批量读取PLC数据
"""

import os
from pathlib import Path

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent

import pandas as pd
import snap7
from snap7.util import *
import struct
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
from loguru import logger


@dataclass
class PointInfo:
    """点位信息"""
    name: str
    db_number: int
    byte_offset: int
    bit_offset: int = 0
    data_type: str = "REAL"
    size: int = 4

    @classmethod
    def from_address(cls, name: str, address: str, data_type: str) -> 'PointInfo':
        """从地址字符串解析点位信息

        例如: "DB5.128.0" -> db=5, offset=128, bit=0
             "DB6.12.0"  -> db=6, offset=12, bit=0
        """
        # 解析地址 DB块号.字节偏移.位偏移
        match = re.match(r'DB(\d+)\.(\d+)\.(\d+)', address)
        if not match:
            raise ValueError(f"无效的地址格式: {address}")

        db_num = int(match.group(1))
        byte_off = int(match.group(2))
        bit_off = int(match.group(3))

        # 根据数据类型确定大小
        if data_type == "REAL":
            size = 4
        elif data_type == "BOOL":
            size = 1
        elif data_type == "INT":
            size = 2
        elif data_type == "DINT":
            size = 4
        else:
            size = 4

        return cls(name=name, db_number=db_num, byte_offset=byte_off,
                  bit_offset=bit_off, data_type=data_type, size=size)


class PointTableReader:
    """点位表批量读取器"""

    def __init__(self, excel_file: str, plc_ip: str = "192.168.0.1",
                 rack: int = 0, slot: int = 1):
        """
        初始化点位表读取器

        Args:
            excel_file: 点位表Excel文件路径
            plc_ip: PLC IP地址
            rack: 机架号
            slot: 槽位号
        """
        self.excel_file = excel_file
        self.plc_ip = plc_ip
        self.rack = rack
        self.slot = slot
        self.client = snap7.client.Client()
        self.points: List[PointInfo] = []
        self.is_connected = False

        # 加载点位表
        self._load_point_table()

    def _load_point_table(self):
        """加载点位表"""
        logger.info(f"正在加载点位表: {self.excel_file}")
        df = pd.read_excel(self.excel_file)

        # 解析点位
        for idx, row in df.iterrows():
            name = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            addr = str(row.iloc[1]) if pd.notna(row.iloc[1]) else ""
            dtype = str(row.iloc[2]) if pd.notna(row.iloc[2]) else ""

            # 跳过无效地址
            if not addr or addr == "nan" or addr == "NaN":
                logger.warning(f"跳过无效地址的点位: {name}")
                continue

            try:
                point = PointInfo.from_address(name, addr, dtype)
                self.points.append(point)
                logger.debug(f"添加点位: {name} -> DB{point.db_number}.{point.byte_offset}.{point.bit_offset} ({dtype})")
            except Exception as e:
                logger.error(f"解析点位失败 {name}: {e}")

        logger.info(f"成功加载 {len(self.points)} 个有效点位")

    def connect(self) -> bool:
        """连接到PLC"""
        try:
            self.client.connect(self.plc_ip, self.rack, self.slot)
            self.is_connected = True
            logger.info(f"成功连接到PLC: {self.plc_ip}")
            return True
        except Exception as e:
            logger.error(f"连接PLC失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.is_connected:
            self.client.disconnect()
            self.is_connected = False
            logger.info("已断开PLC连接")

    def read_point(self, point: PointInfo) -> Optional[any]:
        """读取单个点位"""
        if not self.is_connected:
            logger.error("未连接到PLC")
            return None

        try:
            # 读取数据
            data = self.client.db_read(point.db_number, point.byte_offset, point.size)

            # 解析数据
            if point.data_type == "REAL":
                value = get_real(data, 0)
            elif point.data_type == "BOOL":
                value = get_bool(data, 0, point.bit_offset)
            elif point.data_type == "INT":
                value = get_int(data, 0)
            elif point.data_type == "DINT":
                value = get_dint(data, 0)
            elif point.data_type == "WORD":
                value = get_word(data, 0)
            elif point.data_type == "DWORD":
                value = get_dword(data, 0)
            else:
                value = None

            return value

        except Exception as e:
            logger.error(f"读取点位失败 {point.name}: {e}")
            return None

    def read_all_points(self) -> Dict[str, any]:
        """读取所有点位"""
        if not self.is_connected:
            logger.error("未连接到PLC")
            return {}

        results = {}

        # 按DB块分组读取，提高效率
        db_groups = {}
        for point in self.points:
            if point.db_number not in db_groups:
                db_groups[point.db_number] = []
            db_groups[point.db_number].append(point)

        # 逐个DB块读取
        for db_num, points in db_groups.items():
            # 找到该DB块的最大偏移量
            max_offset = max(p.byte_offset + p.size for p in points)

            try:
                # 一次性读取整个DB块需要的数据
                raw_data = self.client.db_read(db_num, 0, max_offset)

                # 解析各个点位
                for point in points:
                    try:
                        if point.data_type == "REAL":
                            value = get_real(raw_data, point.byte_offset)
                        elif point.data_type == "BOOL":
                            value = get_bool(raw_data, point.byte_offset, point.bit_offset)
                        elif point.data_type == "INT":
                            value = get_int(raw_data, point.byte_offset)
                        elif point.data_type == "DINT":
                            value = get_dint(raw_data, point.byte_offset)
                        elif point.data_type == "WORD":
                            value = get_word(raw_data, point.byte_offset)
                        elif point.data_type == "DWORD":
                            value = get_dword(raw_data, point.byte_offset)
                        else:
                            value = None

                        results[point.name] = value
                        logger.debug(f"{point.name}: {value}")

                    except Exception as e:
                        logger.error(f"解析点位失败 {point.name}: {e}")
                        results[point.name] = None

            except Exception as e:
                logger.error(f"读取DB{db_num}失败: {e}")
                for point in points:
                    results[point.name] = None

        return results

    def print_results(self, results: Dict[str, any]):
        """打印读取结果"""
        print("\n" + "=" * 80)
        print(f"{'序号':<4} {'点位名称':<30} {'地址':<20} {'数值':<15}")
        print("=" * 80)

        for idx, point in enumerate(self.points, 1):
            value = results.get(point.name)
            addr = f"DB{point.db_number}.{point.byte_offset}.{point.bit_offset}"
            value_str = f"{value}" if value is not None else "读取失败"
            print(f"{idx:<4} {point.name:<30} {addr:<20} {value_str:<15}")

        print("=" * 80)

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.disconnect()


def main():
    """主函数"""
    import sys

    # 配置日志
    logger.remove()
    logger.add(sys.stdout, level="INFO")

    print("=" * 80)
    print("PLC点位表批量读取程序")
    print("=" * 80)

    # 创建读取器
    reader = PointTableReader(
        excel_file=str(PROJECT_ROOT / "data" / "点位表.xlsx"),
        plc_ip="192.168.0.1",  # 修改为实际PLC IP
        rack=0,
        slot=1
    )

    # 连接并读取
    with reader:
        results = reader.read_all_points()
        reader.print_results(results)


if __name__ == "__main__":
    main()
