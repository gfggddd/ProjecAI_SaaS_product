"""
Health check и мониторинг для SaaS приложения.
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from logger_config import logger

class HealthChecker:
    """Проверяет здоровье приложения и его компонентов."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.last_error: str = None
        self.error_count = 0
        self.request_count = 0
    
    async def check_all(self) -> Dict[str, Any]:
        """Выполняет все проверки."""
        checks = {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "status": "healthy",
            "components": {}
        }
        
        # Проверка файловой системы
        checks["components"]["filesystem"] = await self._check_filesystem()
        
        # Проверка логирования
        checks["components"]["logging"] = await self._check_logging()
        
        # Проверка конфигурации
        checks["components"]["config"] = await self._check_config()
        
        # Проверка статистики
        checks["statistics"] = {
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": self.error_count / max(1, self.request_count),
            "last_error": self.last_error
        }
        
        # Общий статус
        if any(c.get("status") != "healthy" for c in checks["components"].values()):
            checks["status"] = "degraded"
        
        return checks
    
    async def _check_filesystem(self) -> Dict[str, Any]:
        """Проверяет доступность файловой системы."""
        try:
            required_dirs = ["logs", "chroma_db", "database"]
            missing = [d for d in required_dirs if not Path(d).exists()]
            
            if missing:
                return {
                    "status": "warning",
                    "message": f"Missing directories: {missing}"
                }
            
            # Проверяем возможность писать
            test_file = Path("logs/.health_check")
            test_file.write_text("ok")
            test_file.unlink()
            
            return {"status": "healthy"}
        except Exception as e:
            logger.error(f"Filesystem check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_logging(self) -> Dict[str, Any]:
        """Проверяет доступность логирования."""
        try:
            log_file = Path("logs/app.log")
            if not log_file.exists():
                return {"status": "warning", "message": "Log file not created yet"}
            
            # Проверяем размер лога (не должен быть слишком большой)
            size_mb = log_file.stat().st_size / (1024 * 1024)
            if size_mb > 1000:  # > 1 GB
                return {
                    "status": "warning",
                    "message": f"Log file is large: {size_mb:.2f} MB"
                }
            
            return {"status": "healthy", "size_mb": size_mb}
        except Exception as e:
            logger.error(f"Logging check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def _check_config(self) -> Dict[str, Any]:
        """Проверяет конфигурацию."""
        try:
            from config_new import DEEPSEEK_API_KEY, ENVIRONMENT
            
            if not DEEPSEEK_API_KEY:
                return {
                    "status": "unhealthy",
                    "message": "DEEPSEEK_API_KEY not configured"
                }
            
            return {
                "status": "healthy",
                "environment": ENVIRONMENT
            }
        except Exception as e:
            logger.error(f"Config check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    def record_request(self):
        """Регистрирует успешный запрос."""
        self.request_count += 1
    
    def record_error(self, error: str):
        """Регистрирует ошибку."""
        self.error_count += 1
        self.last_error = error
        logger.error(f"Error recorded: {error}")

# Глобальный экземпляр
health_checker = HealthChecker()
