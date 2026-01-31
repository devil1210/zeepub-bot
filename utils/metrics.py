import logging

from prometheus_client import Counter, Gauge, Histogram, start_http_server

logger = logging.getLogger(__name__)


class MetricsManager:
    """
    Gestor centralizado de métricas Prometheus.
    Expone un servidor HTTP ligero para scraping si se configuran puertos.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.enabled = True  # Podría ser config.ENABLE_METRICS

        # Definición de métricas estándar

        # Contadores
        self.downloads_total = Counter(
            "zeepub_downloads_total",
            "Total de descargas solicitadas",
            [
                "status",
                "user_type",
            ],  # status: success, failed. user_type: admin, vip, user
        )
        self.commands_total = Counter(
            "zeepub_commands_total", "Total de comandos ejecutados", ["command"]
        )
        self.errors_total = Counter(
            "zeepub_errors_total", "Total de errores manejados", ["type"]
        )

        # Histogramas
        self.request_duration_seconds = Histogram(
            "zeepub_request_duration_seconds",
            "Tiempo de procesamiento de solicitudes",
            ["handler"],
        )
        self.download_duration_seconds = Histogram(
            "zeepub_download_duration_seconds",
            "Tiempo de descarga de libros externos",
            ["source"],
        )

        # Gauges
        self.active_users = Gauge(
            "zeepub_active_users", "Usuarios activos estimados (última hora)"
        )

    def start_server(self, port: int = 8000):
        """Inicia el servidor de métricas en un puerto separado."""
        if not self.enabled:
            return
        try:
            start_http_server(port)
            logger.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")

    # Helpers para uso fácil
    def inc_download(self, status: str = "success", user_type: str = "user"):
        self.downloads_total.labels(status=status, user_type=user_type).inc()

    def inc_command(self, command: str):
        self.commands_total.labels(command=command).inc()

    def inc_error(self, error_type: str):
        self.errors_total.labels(type=error_type).inc()


metrics = MetricsManager()
