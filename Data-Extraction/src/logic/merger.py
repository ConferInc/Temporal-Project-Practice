"""
Document Merger — Merge flat dicts from multiple document extractions.

Resolves conflicts using document-priority (verified > stated) and
performs cross-document party matching using SSN (exact) and name (fuzzy).

Dependencies: stdlib only (difflib for fuzzy matching — no AI libraries)
"""

from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logging import logger


class DocumentMerger:
    """Merge flat dicts from multiple document extractions."""

    # Document priority: higher = more authoritative
    # Verified documents overwrite borrower-stated values
    PRIORITY: Dict[str, int] = {
        "W-2 Form": 90,             # IRS-verified
        "Appraisal (Form 1004)": 85, # appraiser-verified
        "Pay Stub": 80,             # employer-verified
        "Tax Return (1040)": 70,     # IRS filing
        "Bank Statement": 60,       # bank-verified
        "URLA (Form 1003)": 50,     # borrower-stated
        "Loan Estimate": 40,        # lender-generated
        "Loan Estimate (H-24)": 40,
    }

    # SSN-bearing flat keys per document type
    _SSN_KEYS: Dict[str, List[str]] = {
        "W-2 Form": ["w2_employee_ssn"],
        "URLA (Form 1003)": ["urla_borrower_ssn", "urla_coborrower_ssn"],
        "Tax Return (1040)": ["tax_taxpayer_ssn", "tax_spouse_ssn"],
        "Pay Stub": [],  # paystub doesn't usually have SSN
        "Bank Statement": [],
        "Appraisal (Form 1004)": [],
        "Loan Estimate": [],
    }

    # Name-bearing flat keys per document type
    _NAME_KEYS: Dict[str, List[str]] = {
        "W-2 Form": ["w2_employee_full_name", "w2_employee_first_name"],
        "URLA (Form 1003)": ["urla_borrower_name", "urla_coborrower_name"],
        "Tax Return (1040)": ["tax_taxpayer_first_name", "tax_spouse_first_name"],
        "Pay Stub": ["paystub_employee_name"],
        "Bank Statement": ["bank_account_holder"],
        "Appraisal (Form 1004)": ["appraisal_borrower_name"],
        "Loan Estimate": ["le_applicant_names"],
    }

    # Name similarity threshold for fuzzy matching
    NAME_THRESHOLD: float = 0.80

    def merge(self, extractions: List[Tuple[str, dict]]) -> dict:
        """Merge multiple (doc_type, flat_dict) tuples into one flat dict.

        Documents are applied in ascending priority order so that
        higher-priority documents overwrite lower-priority values
        for the same keys.

        Args:
            extractions: list of (doc_type, flat_dict) tuples

        Returns:
            Merged flat dict with all keys from all documents
        """
        if not extractions:
            return {}

        # Sort by priority ascending (lowest first, highest overwrites)
        sorted_extractions = sorted(
            extractions,
            key=lambda x: self.PRIORITY.get(x[0], 0),
        )

        merged: Dict[str, Any] = {}
        sources: Dict[str, str] = {}  # track which doc set each key

        for doc_type, flat in sorted_extractions:
            for key, value in flat.items():
                if value is not None:
                    prev_source = sources.get(key)
                    if prev_source and prev_source != doc_type:
                        logger.debug(
                            f"Merge conflict: '{key}' overwritten by "
                            f"'{doc_type}' (was '{prev_source}')"
                        )
                    merged[key] = value
                    sources[key] = doc_type

        logger.info(
            f"DocumentMerger merged {len(merged)} keys from "
            f"{len(extractions)} documents"
        )
        return merged

    def match_parties(
        self, extractions: List[Tuple[str, dict]]
    ) -> Dict[str, str]:
        """Cross-document party matching using SSN (exact) and name (fuzzy).

        Returns a mapping: {doc_party_key: canonical_party_id}
        where canonical_party_id groups the same person across documents.

        Example output:
            {
                "w2_employee": "party_0",
                "urla_borrower": "party_0",
                "urla_coborrower": "party_1",
                "tax_taxpayer": "party_0",
                "tax_spouse": "party_1",
            }
        """
        # Collect all party evidence: (party_label, ssn, name)
        party_evidence: List[Tuple[str, Optional[str], Optional[str]]] = []

        for doc_type, flat in extractions:
            ssn_keys = self._SSN_KEYS.get(doc_type, [])
            name_keys = self._NAME_KEYS.get(doc_type, [])

            for i, ssn_key in enumerate(ssn_keys):
                ssn = flat.get(ssn_key)
                name = flat.get(name_keys[i]) if i < len(name_keys) else None
                label = ssn_key.rsplit("_ssn", 1)[0]  # e.g. "w2_employee"
                if ssn or name:
                    party_evidence.append((label, ssn, name))

            # Also check name-only keys that don't have SSN counterparts
            for j, name_key in enumerate(name_keys):
                if j >= len(ssn_keys):
                    name = flat.get(name_key)
                    label = name_key.rsplit("_name", 1)[0]
                    if label.endswith("_full"):
                        label = label.rsplit("_full", 1)[0]
                    if name:
                        party_evidence.append((label, None, name))

        if not party_evidence:
            return {}

        # Build party clusters
        clusters: List[List[str]] = []  # each cluster is a list of labels
        cluster_ssns: List[Optional[str]] = []
        cluster_names: List[Optional[str]] = []

        for label, ssn, name in party_evidence:
            matched_cluster = None

            # Try SSN exact match first
            if ssn:
                for idx, c_ssn in enumerate(cluster_ssns):
                    if c_ssn and self._normalize_ssn(ssn) == self._normalize_ssn(c_ssn):
                        matched_cluster = idx
                        break

            # Try name fuzzy match
            if matched_cluster is None and name:
                for idx, c_name in enumerate(cluster_names):
                    if c_name and self._name_similarity(name, c_name) >= self.NAME_THRESHOLD:
                        matched_cluster = idx
                        break

            if matched_cluster is not None:
                clusters[matched_cluster].append(label)
                # Update SSN/name if we have better data
                if ssn and not cluster_ssns[matched_cluster]:
                    cluster_ssns[matched_cluster] = ssn
                if name and not cluster_names[matched_cluster]:
                    cluster_names[matched_cluster] = name
            else:
                # New cluster
                clusters.append([label])
                cluster_ssns.append(ssn)
                cluster_names.append(name)

        # Build result mapping
        result: Dict[str, str] = {}
        for idx, cluster in enumerate(clusters):
            party_id = f"party_{idx}"
            for label in cluster:
                result[label] = party_id

        logger.info(
            f"Party matching: {len(party_evidence)} evidence items -> "
            f"{len(clusters)} unique parties"
        )
        return result

    @staticmethod
    def _normalize_ssn(ssn: str) -> str:
        """Remove dashes and spaces from SSN for comparison."""
        return ssn.replace("-", "").replace(" ", "").strip()

    @staticmethod
    def _name_similarity(name1: str, name2: str) -> float:
        """Compute name similarity using SequenceMatcher."""
        n1 = name1.upper().strip()
        n2 = name2.upper().strip()
        return SequenceMatcher(None, n1, n2).ratio()
