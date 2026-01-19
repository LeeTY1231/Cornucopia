import sys
import argparse
from datetime import datetime
from src.data.data_manager import DataManager

# 初始化日志系统
setup_logger()
logger = get_logger(__name__)

"""
Cornucopia
   A type of stock trading system which based on Python.
   This is an open source system.

Author: 李腾越-Li.Teng-yue Leety
Email: lty15517502979@163.com
StartTime: 2026-01-18
Version: 1.0.0
"""

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        sys.exit(1)
