"""Background jobs the controller runs off the GUI thread.

Every worker follows the same contract, which is what AppController._start_worker
relies on: a ``run`` slot that does the blocking call, a result signal, and a
``finished`` signal emitted in a ``finally`` so the thread is always torn down
even when the job raises.

They live here rather than in controller.py because they share no state with the
controller: each one takes what it needs at construction and reaches straight for
a service.
"""

from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import QObject, Signal, Slot

from .ai_provider import AiProviderService
from .application import CoinductorApplication
from .assistant import ProviderBackedAssistant
from .connection_check import ConnectionCheckService, LiveTradingCheckService, TestnetCheckService
from .first_portfolio_executor import FirstPortfolioExecutor
from .models import RunOptions


class AnalysisWorker(QObject):
    progress = Signal(str, int)
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, options: RunOptions):
        super().__init__()
        self.options = options

    @Slot()
    def run(self) -> None:
        try:
            result = CoinductorApplication().run_analysis(
                self.options,
                lambda message, percent: self.progress.emit(message, percent),
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class ConnectionCheckWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(ConnectionCheckService(language=self.language).check_binance_read_only())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class LiveTradingCheckWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(LiveTradingCheckService(language=self.language).check_binance_live_trading())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class TestnetCheckWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, language: str = "en"):
        super().__init__()
        self.language = language

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(TestnetCheckService(language=self.language).check_binance_testnet())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class FirstPortfolioTrancheWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        asset: str,
        target_pct: Decimal,
        total_budget: Decimal,
        tranche_index: int,
        tranches_total: int,
        mode: str,
        submit: bool,
        confirm: str,
    ):
        super().__init__()
        self.asset = asset
        self.target_pct = target_pct
        self.total_budget = total_budget
        self.tranche_index = tranche_index
        self.tranches_total = tranches_total
        self.mode = mode
        self.submit = submit
        self.confirm = confirm

    @Slot()
    def run(self) -> None:
        try:
            result = FirstPortfolioExecutor().run_tranche(
                asset=self.asset,
                target_pct=self.target_pct,
                total_budget=self.total_budget,
                tranche_index=self.tranche_index,
                tranches_total=self.tranches_total,
                mode=self.mode,
                submit=self.submit,
                confirm=self.confirm,
            )
            self.completed.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AiProviderHealthWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(AiProviderService().health_check())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class LocalAiHardwareWorker(QObject):
    """Reads RAM/GPU by shelling out to OS tools, which can take seconds.

    On the GUI thread that froze the whole window until it returned.
    """

    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    @Slot()
    def run(self) -> None:
        try:
            from .local_ai_recommender import LocalAiRecommender  # noqa: PLC0415

            self.completed.emit(LocalAiRecommender().inspect())
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AiModelDiscoveryWorker(QObject):
    completed = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, base_url: str, api_key: str = ""):
        super().__init__()
        self.base_url = base_url
        self.api_key = api_key

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(AiProviderService().discover_models(self.base_url, self.api_key))
        except Exception as exc:
            self.failed.emit(str(exc))
        finally:
            self.finished.emit()


class AssistantWorker(QObject):
    completed = Signal(object)
    finished = Signal()

    def __init__(
        self,
        question: str,
        snapshot,
        app_context: dict[str, object],
        conversation: tuple[dict[str, str], ...],
        image_path: str,
    ):
        super().__init__()
        self.question = question
        self.snapshot = snapshot
        self.app_context = app_context
        self.conversation = conversation
        self.image_path = image_path

    @Slot()
    def run(self) -> None:
        try:
            self.completed.emit(
                ProviderBackedAssistant().respond(
                    self.question,
                    self.snapshot,
                    self.app_context,
                    self.conversation,
                    self.image_path,
                )
            )
        finally:
            self.finished.emit()
