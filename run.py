#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Единая точка входа для Scalingo с Flask для health checks и Telegram ботом
"""

import asyncio
import threading
import logging
from flask import Flask
import os
from weather_bot import start_bot

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask приложение для health checks
app = Flask(__name__)

@app.route('/')
def index():
    return 'Weather Bot is running', 200

@app.route('/health')
def health():
    return 'OK', 200

def run_flask():
    """Запуск Flask приложения"""
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def run_bot():
    """Запуск Telegram бота"""
    logger.info("Starting Telegram bot...")
    asyncio.run(start_bot())

if __name__ == '__main__':
    logger.info("🌤️ Starting Weather Bot application...")
    
    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask server thread started")
    
    # Запускаем бота в основном потоке
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
        raise
