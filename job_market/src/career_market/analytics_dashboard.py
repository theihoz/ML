"""Presentation caches keyed by raw evidence and label ledger bytes."""

import hashlib

import streamlit as st

from .preparation import RULES_VERSION
from .service import MarketError, MarketService
from .training_labels import data_root


def evidence_signature():
    try:
        return _read_signature()
    except OSError as error:
        raise MarketError("Không đọc được dữ liệu thống kê.") from error


def _read_signature():
    root = data_root()
    paths = (
        sorted((root / "raw").glob("*.csv"))
        + sorted((root / "labels/2026-10-29").glob("*.json"))
        + sorted((root / "labels/2026-10-29").glob("*.csv"))
    )
    return (
        RULES_VERSION,
        tuple((str(path), hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths),
    )


@st.cache_data(show_spinner=False)
def _salary_report(cohort, charts, signature):
    return MarketService().salary_analysis(cohort, charts)


def salary_report(cohort, charts):
    return _salary_report(cohort, tuple(charts), evidence_signature())


@st.cache_data(show_spinner=False)
def _overview(signature):
    return MarketService().market_overview()


def overview_report():
    return _overview(evidence_signature())
