from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any


def est_tokens(text: str) -> int:
    """
    Lightweight token estimate: ~ 4 chars/token (rough), with floor.
    It's approximate but useful for cost tracking and comparisons.
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))


@dataclass
class CostEstimate:
    input_tokens_est: int
    output_tokens_est: int
    total_tokens_est: int
    cost_est_usd: float


class UsageLogger:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts INTEGER NOT NULL,
                    request_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    task TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    input_tokens_est INTEGER NOT NULL,
                    output_tokens_est INTEGER NOT NULL,
                    total_tokens_est INTEGER NOT NULL,
                    cost_est_usd REAL NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    success INTEGER NOT NULL,
                    error TEXT
                );
                """
            )
            con.commit()
        finally:
            con.close()

    def log(
        self,
        *,
        request_id: str,
        provider: str,
        model: str,
        task: str,
        priority: str,
        estimate: CostEstimate,
        latency_ms: int,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            cur = con.cursor()
            cur.execute(
                """
                INSERT INTO usage_logs (
                    ts, request_id, provider, model, task, priority,
                    input_tokens_est, output_tokens_est, total_tokens_est,
                    cost_est_usd, latency_ms, success, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    int(time.time()),
                    request_id,
                    provider,
                    model,
                    task,
                    priority,
                    estimate.input_tokens_est,
                    estimate.output_tokens_est,
                    estimate.total_tokens_est,
                    estimate.cost_est_usd,
                    latency_ms,
                    1 if success else 0,
                    error,
                ),
            )
            con.commit()
        finally:
            con.close()


def estimate_cost(
    *,
    provider: str,
    prompt: str,
    output_text: str,
    cost_per_1k_input_usd: float,
    cost_per_1k_output_usd: float,
) -> CostEstimate:
    in_tok = est_tokens(prompt)
    out_tok = est_tokens(output_text)
    total = in_tok + out_tok
    cost = (in_tok / 1000.0) * cost_per_1k_input_usd + (out_tok / 1000.0) * cost_per_1k_output_usd
    return CostEstimate(
        input_tokens_est=in_tok,
        output_tokens_est=out_tok,
        total_tokens_est=total,
        cost_est_usd=round(cost, 8),
    )
