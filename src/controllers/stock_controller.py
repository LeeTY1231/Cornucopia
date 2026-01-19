
from flask import Blueprint, jsonify, request
import logging
from src.services.stock_service import StockService

stock_controller = Blueprint('stock', __name__, url_prefix='/api/cornucopia/stock')

# 配置日志
logger = logging.getLogger(__name__)

@stock_controller.route('/test', methods=['GET'])
def test():
    """
    Test接口
    用于测试API服务是否正常运行
    """
    try:
        logger.info("Test接口被调用")
        
        stock_service = StockService()
        stock_service.updatestockmodel()
        # 返回测试响应
        response_data = {
            "status": "success",
            "message": "股票API服务正常运行",
            "data": {
                "service": "Cornucopia Stock API",
                "version": "1.0.0",
                "timestamp": "2026-01-18"
            }
        }
        
        return jsonify(response_data), 200
    
    except Exception as e:
        logger.error(f"Test接口异常: {e}")
        return jsonify({
            "status": "error",
            "message": "服务器内部错误",
            "error": str(e)
        }), 500
    

__all__ = [
    'stock_controller'
]