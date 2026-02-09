"""
AI Underwriting Brain Module

This package implements the GenAI document processing pipeline
using Docling for PDF ingestion and LangGraph for agent orchestration.

Components:
- schemas: Pydantic models for structured AI outputs
- ingestion: PDF-to-Markdown conversion via Docling
- brain: LangGraph agent (Extract -> Reason -> Decide)
"""
from app.ai.schemas import IncomeAnalysis, ExtractedFinancials, UnderwritingDecision
from app.ai.ingestion import parse_document
from app.ai.brain import run_underwriter_agent

__all__ = [
    "IncomeAnalysis",
    "ExtractedFinancials",
    "UnderwritingDecision",
    "parse_document",
    "run_underwriter_agent",
]
