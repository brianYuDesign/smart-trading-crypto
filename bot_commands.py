"""
Telegram Bot 指令處理程式
單獨運行，用於處理用戶互動指令
"""

import os
import sys

# 將 src 目錄加入路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_commands import TelegramCommandHandler


def main():
    """主程式 - 處理 Telegram 指令"""
    print("\n" + "=" * 70)
    print("🤖 Telegram Bot 指令處理器")
    print("=" * 70)

    handler = TelegramCommandHandler()
    handler.process_updates()

    print("\n✅ 指令處理完成")


if __name__ == '__main__':
    main()
