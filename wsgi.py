import os
from src.server import app, init_app_monitor

# 初始化監控組件 (啟動背景線程)
init_app_monitor()

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
