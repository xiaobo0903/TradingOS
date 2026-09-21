#!/usr/bin/env python3
"""
数据库初始化脚本
"""
import sys
import os

# 将项目根目录添加到 Python 路径 (backend 的父目录)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from models.database import init_db

if __name__ == "__main__":
    print("正在创建数据库表...")
    init_db()
    print("数据库表创建完成!")
