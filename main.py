import sys
import argparse
from datetime import datetime
from venv import logger
from flask import Flask
from src.controllers.stock_controller import stock_controller
from src.data.data_manager import DataManager

"""
Cornucopia
   A type of stock trading system which based on Python.
   This is an open source system.

Author: 李腾越-Li.Teng-yue Leety
Email: lty15517502979@163.com
StartTime: 2026-01-18
Version: 1.0.0
"""
def Interface():
    interface = Flask(__name__)
    interface.register_blueprint(stock_controller)
    @interface.route('/')
    def index():
        return {
            "service": "Cornucopia Stock API",
            "version": "1.0.0",
            "description": "基于Python的股票交易系统API服务"
        }
    return interface

def main():
    app = Interface()
    app.run(host='localhost', port=5038, debug=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序异常退出: {e}", exc_info=True)
        sys.exit(1)
