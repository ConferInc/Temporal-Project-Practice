"""
Rule Engine — Universal Deterministic Text-to-Canonical-JSON extractor.

Supports TWO input modes driven by YAML configuration files:
  Mode A (Markdown/Docling): heading, key_value, table rules
  Mode B (OCR/Plain text):   checkbox, positional, section rules

Common rule types (both modes):
  regex      – Apply regex patterns with capture groups
  static     – Inject a constant value
  computed   – Copy/transform a previously extracted value

Dependencies: re, json, yaml  (stdlib + PyYAML — NO AI libraries)
"""

import os
import re
import json
import copy
from typing import Any, Dict, List, Optional, Tuple

import yaml

from src.utils.logging import logger


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_nested(target: dict, dotted_path: str, value: Any) -> None:
    """
    Set a value deep inside a nested dict using a dotted path that may
    include array indices, e.g. 'deal.parties[0].employment[0].employer_name'.
    Intermediate dicts / lists are created as needed.
    """
    parts = _split_path(dotted_path)
    current = target
    for i, part in enumerate(parts[:-1]):
        key, idx = _parse_part(part)
        if key not in current:
            if idx is not None:
                current[key] = []
            else:
                current[key] = {}
        node = current[key]
        if idx is not None:
            while len(node) <= idx:
                node.append({})
            current = node[idx]
        else:
            current = node

    leaf = parts[-1]
    key, idx = _parse_part(leaf)
    if idx is not None:
        if key not in current:
            current[key] = []
        while len(current[key]) <= idx:
            current[key].append(None)
        current[key][idx] = value
    else:
        current[key] = value


def _get_nested(source: dict, dotted_path: str) -> Any:
    """Read a value from a nested dict using a dotted path."""
    parts = _split_path(dotted_path)
    current = source
    for part in parts:
        if current is None:
            return None
        key, idx = _parse_part(part)
        current = current.get(key) if isinstance(current, dict) else None
        if current is None:
            return None
        if idx is not None:
            if isinstance(current, list) and idx < len(current):
                current = current[idx]
            else:
                return None
    return current


def _split_path(path: str) -> List[str]:
    return path.split(".")


def _parse_part(part: str) -> Tuple[str, Optional[int]]:
    m = re.match(r"^(.+?)\[(\d+)\]$", part)
    if m:
        return m.group(1), int(m.group(2))
    return part, None


def _clean_currency(text: str) -> Optional[float]:
    """Convert '$1,627.74' or '1,627.74' to 1627.74."""
    if text is None:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", text.strip())
    if not cleaned:
        return None
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def _clean_number(text: str) -> Optional[float]:
    if text is None:
        return None
    cleaned = re.sub(r"[^\d.\-]", "", text.strip())
    if not cleaned:
        return None
    try:
        return round(float(cleaned), 4)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Markdown Table Parser  (Mode A)
# ---------------------------------------------------------------------------

def _parse_markdown_tables(markdown: str) -> List[List[List[str]]]:
    tables: List[List[List[str]]] = []
    lines = markdown.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and line.endswith("|"):
            table_rows: List[List[str]] = []
            while i < len(lines):
                row_line = lines[i].strip()
                if not (row_line.startswith("|") and row_line.endswith("|")):
                    break
                cells = [c.strip() for c in row_line.split("|")]
                cells = cells[1:-1]
                if cells and all(re.match(r"^[-:]+$", c) for c in cells if c):
                    i += 1
                    continue
                table_rows.append(cells)
                i += 1
            if table_rows:
                tables.append(table_rows)
        else:
            i += 1
    return tables


def _find_table_by_headers(
    tables: List[List[List[str]]],
    header_keywords: List[str],
) -> Optional[List[List[str]]]:
    for table in tables:
        header_text = " ".join(
            " ".join(row) for row in table[:min(3, len(table))]
        ).upper()
        if all(kw.upper() in header_text for kw in header_keywords):
            return table
    return None


# ---------------------------------------------------------------------------
# OCR Checkbox Helpers  (Mode B)
# ---------------------------------------------------------------------------

# Common OCR artifacts for checked boxes: XI, Xl, [X], (X), ☑, ☒
_CHECKBOX_MARKS = re.compile(
    r"(?:XI|Xl|X[lI]|\[X\]|\(X\)|☑|☒)",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Rule Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """
    Universal deterministic rule-based extractor.

    Usage:
        engine = RuleEngine()
        canonical = engine.extract(text_string, "Pay Stub")
        canonical = engine.extract(ocr_string, "URLA (Form 1003)")

        # Flat mode — returns {business_key: value} dict
        flat = engine.extract(text_string, "W-2 Form", output_mode="flat")
    """

    RULES_DIR = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "rules",
    )

    def __init__(self, rules_dir: Optional[str] = None):
        self._rules_dir = rules_dir or self.RULES_DIR
        self._config_cache: Dict[str, dict] = {}
        self._output_mode: str = "nested"

    # ================================================================
    #  PUBLIC API
    # ================================================================

    def extract(
        self, text: str, document_type: str, output_mode: str = "nested"
    ) -> Dict[str, Any]:
        """Run all rules for *document_type* against *text*.

        Args:
            text: raw text (markdown or OCR)
            document_type: classifier label (e.g. "Pay Stub")
            output_mode: "nested" (default, backward-compatible) or "flat"
                         (returns {business_key: value} dict)
        """
        self._output_mode = output_mode
        config = self._load_config(document_type)
        if config is None:
            logger.warning(
                f"No rule config found for '{document_type}'. Returning empty."
            )
            return {}

        rules = config.get("rules", [])
        result: Dict[str, Any] = {}

        # Pre-parse markdown tables (cheap no-op on plain OCR text)
        tables = _parse_markdown_tables(text)

        for rule in rules:
            rule_id = rule.get("id", "unnamed")
            rule_type = rule.get("type")
            try:
                handler = self._DISPATCH.get(rule_type)
                if handler:
                    handler(self, rule, text, tables, result)
                else:
                    logger.warning(f"Unknown rule type '{rule_type}' in '{rule_id}'")
            except Exception as exc:
                logger.error(f"Rule '{rule_id}' failed: {exc}")

        logger.info(
            f"RuleEngine extracted {self._count_fields(result)} fields "
            f"for '{document_type}' (mode={output_mode})"
        )
        return result

    # ================================================================
    #  VALUE ROUTING  (flat vs nested)
    # ================================================================

    def _set_value(self, rule: dict, result: dict, value: Any) -> None:
        """Route value to flat key or nested target_path based on output_mode."""
        if self._output_mode == "flat" and "key" in rule:
            result[rule["key"]] = value
        elif "target_path" in rule:
            _set_nested(result, rule["target_path"], value)

    def _set_value_at(self, rule: dict, result: dict, value: Any,
                      target_path: str) -> None:
        """Route value with an explicit target_path override (for multi-group rules)."""
        if self._output_mode == "flat" and "key" in rule:
            # For multi-group regex, key is set per-group via groups_keys
            # This fallback stores at rule["key"] only for single-group usage
            result[rule["key"]] = value
        else:
            _set_nested(result, target_path, value)

    # ================================================================
    #  CONFIG LOADING
    # ================================================================

    # Explicit aliases: classifier document_type -> YAML filename (without .yaml)
    _ALIASES: Dict[str, str] = {
        "W-2 Form":              "W-2Form",
        "Tax Return (1040)":     "TaxReturn",
        "Appraisal (Form 1004)": "Appraisal",
        "Loan Estimate":         "LoanEstimate",
        "Loan Estimate (H-24)":  "LoanEstimate",
        "1099-MISC":             "1099 misc",  # Maps to "1099 misc.yaml"
        "Closing Disclosure":    "ClosingDisclosure",
    }

    def _load_config(self, document_type: str) -> Optional[dict]:
        if document_type in self._config_cache:
            return self._config_cache[document_type]

        # Try explicit alias first
        candidates = []
        alias = self._ALIASES.get(document_type)
        if alias:
            candidates.append(alias + ".yaml")

        # Then try multiple filename conventions
        candidates += [
            document_type.replace(" ", "") + ".yaml",
            document_type.replace(" ", "_") + ".yaml",
        ]
        # Handle "URLA (Form 1003)" -> "URLA.yaml"
        base = document_type.split("(")[0].strip().replace(" ", "")
        if base + ".yaml" not in candidates:
            candidates.insert(0, base + ".yaml")

        path = None
        for fname in candidates:
            p = os.path.join(self._rules_dir, fname)
            if os.path.isfile(p):
                path = p
                break

        if path is None:
            logger.warning(f"Rule config not found for '{document_type}' "
                           f"(tried: {candidates})")
            return None

        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        self._config_cache[document_type] = config
        return config

    # ================================================================
    #  MODE A — MARKDOWN RULES
    # ================================================================

    def _apply_heading(self, rule, text, _tables, result):
        level = rule.get("level", 2)
        prefix = "#" * level
        pattern = rf"^{re.escape(prefix)}\s+(.+)$"
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            value = match.group(1).strip()
            self._set_value(rule, result, value)
            logger.debug(f"heading -> {rule.get('key') or rule.get('target_path')} = {value!r}")

    def _apply_key_value(self, rule, text, _tables, result):
        kv_key = re.escape(rule["key"])
        target = rule.get("target_path", "")
        # Pattern 1: Docling newline-separated "Key:\n\nValue"
        p1 = rf"(?:^|\n)\s*(?:\*\*)?{kv_key}(?:\*\*)?\s*:\s*\n\s*\n\s*(.+?)(?:\n|$)"
        match = re.search(p1, text)
        if not match:
            # Pattern 2: Same-line "Key: Value"
            p2 = rf"(?:^|\n)\s*(?:\*\*)?{kv_key}(?:\*\*)?\s*:\s*(.+?)(?:\n|$)"
            match = re.search(p2, text)
        if match:
            value = match.group(1).strip()
            if value:
                self._set_value(rule, result, value)
                logger.debug(f"key_value -> {rule.get('key') or target} = {value!r}")

    def _apply_table(self, rule, _text, tables, result):
        identify = rule.get("identify_by", {})
        keywords = identify.get("header_contains", [])
        table = _find_table_by_headers(tables, keywords)
        if table is None:
            logger.debug(f"Table '{rule.get('id')}': no match for {keywords}")
            return

        col_index = self._build_column_index(table)

        # Mode 1: specific cells
        if "extract" in rule:
            # In flat mode, use keys_map from the rule if available
            flat_keys_map = rule.get("extract_keys", {}) if self._output_mode == "flat" else {}
            for spec in rule["extract"]:
                row_label = spec.get("row_label", "")
                data_row = self._find_row_by_label(table, row_label)
                if data_row is None:
                    continue
                for col_name, target_path in spec.get("columns", {}).items():
                    col_idx = col_index.get(col_name.upper())
                    if col_idx is not None and col_idx < len(data_row):
                        raw_value = data_row[col_idx].strip()
                        value = _clean_currency(raw_value)
                        if value is not None:
                            if self._output_mode == "flat":
                                flat_key = flat_keys_map.get(target_path)
                                if flat_key:
                                    result[flat_key] = value
                                elif "key" in rule:
                                    # Fallback: use rule-level key with suffix
                                    result[f"{rule['key']}_{row_label}_{col_name}".lower().replace(" ", "_")] = value
                                else:
                                    _set_nested(result, target_path, value)
                            else:
                                _set_nested(result, target_path, value)

        # Mode 2: all data rows
        if "extract_rows" in rule:
            rs = rule["extract_rows"]
            target_path = rs["target_path"]
            flat_key = rs.get("flat_key", rule.get("key"))
            skip_total = rs.get("skip_total", True)
            column_map = rs.get("column_map", {})
            col_offset = int(rs.get("col_offset", 0))
            string_cols = set(rs.get("string_columns", []))
            skip_header = int(rs.get("skip_header_rows", 0))

            data_start = skip_header if skip_header > 0 else self._find_data_start(table)
            extracted_rows = []
            for row in table[data_start:]:
                first_idx = col_offset
                first_cell = row[first_idx].strip() if first_idx < len(row) else ""
                if not first_cell:
                    continue
                if skip_total and "TOTAL" in first_cell.upper():
                    continue
                row_dict = {}
                for col_idx_str, field_name in column_map.items():
                    col_idx = int(col_idx_str) + col_offset
                    if col_idx < len(row):
                        raw = row[col_idx].strip()
                        if raw:
                            if field_name in string_cols:
                                row_dict[field_name] = raw
                            else:
                                num = _clean_number(raw)
                                row_dict[field_name] = num if num is not None else raw
                if row_dict:
                    extracted_rows.append(row_dict)
            if extracted_rows:
                if self._output_mode == "flat" and flat_key:
                    result[flat_key] = extracted_rows
                else:
                    _set_nested(result, target_path, extracted_rows)

    # ================================================================
    #  MODE B — OCR / PLAIN-TEXT RULES
    # ================================================================

    def _apply_checkbox(self, rule, text, _tables, result):
        """
        Detect which option in a group is 'checked' in OCR text.

        YAML spec:
            type: checkbox
            label: "Purpose of Loan"        # anchor text
            options:                         # candidate values
              - match: "Purchase"
                value: "Purchase"
              - match: "Refinance"
                value: "Refinance"
              - match: "Construction"
                value: "Construction"
            target_path: "deal.transaction_information.loan_purpose.value"

        Detection logic — for each option, look for a checkbox mark
        (XI, [X], etc.) immediately before the match keyword within
        a window around the label.
        """
        label = rule.get("label", "")
        options = rule.get("options", [])
        target = rule["target_path"]
        # Window: up to `window_lines` lines around the label
        window = int(rule.get("window_lines", 5))

        # Find the label in text
        lines = text.split("\n")
        label_idx = None
        for i, line in enumerate(lines):
            if label.lower() in line.lower():
                label_idx = i
                break

        if label_idx is None:
            logger.debug(f"checkbox '{rule.get('id')}': label '{label}' not found")
            return

        # Build the search window
        start = max(0, label_idx - 1)
        end = min(len(lines), label_idx + window + 1)
        window_text = "\n".join(lines[start:end])

        for opt in options:
            match_kw = opt["match"]
            # Look for checkbox mark immediately before the keyword
            # e.g. "XI Purchase" or "[X] Purchase" or "☑ Purchase"
            pattern = (
                r"(?:XI|Xl|X[lI]|\[X\]|\(X\)|☑|☒)\s*"
                + re.escape(match_kw)
            )
            if re.search(pattern, window_text, re.IGNORECASE):
                self._set_value(rule, result, opt["value"])
                logger.debug(f"checkbox -> {rule.get('key') or target} = {opt['value']!r}")
                return

        # Fallback: check for the mark pattern anywhere in the window
        # and use the first option whose keyword is nearby
        for opt in options:
            match_kw = opt["match"]
            if match_kw.lower() in window_text.lower():
                # Check if there's any checkbox mark on the same line
                for line in lines[start:end]:
                    if match_kw.lower() in line.lower() and _CHECKBOX_MARKS.search(line):
                        self._set_value(rule, result, opt["value"])
                        logger.debug(f"checkbox (fallback) -> {rule.get('key') or target} = {opt['value']!r}")
                        return

    def _apply_positional(self, rule, text, _tables, result):
        """
        Find an anchor keyword, then capture text relative to it.

        YAML spec:
            type: positional
            anchor: "Social Security Number"
            direction: below          # below | right | after
            skip_lines: 1             # how many lines to skip after anchor
            capture_pattern: '\d{3}-\d{2}-\d{4}'  # regex for the value
            target_path: "deal.parties[0].individual.ssn"
            transform: null

        For direction=after:
            Captures inline text after the anchor on the same line,
            optionally filtered by capture_pattern.

        For direction=below:
            Scans lines below the anchor (skipping skip_lines).
        """
        anchor = rule.get("anchor", "")
        direction = rule.get("direction", "below")
        skip = int(rule.get("skip_lines", 0))
        cap_pattern = rule.get("capture_pattern")
        target = rule["target_path"]
        transform = rule.get("transform")

        lines = text.split("\n")
        anchor_idx = None
        for i, line in enumerate(lines):
            if anchor.lower() in line.lower():
                anchor_idx = i
                break

        if anchor_idx is None:
            logger.debug(f"positional '{rule.get('id')}': anchor '{anchor}' not found")
            return

        value = None

        if direction == "after" or direction == "right":
            # Capture on the same line, after the anchor keyword
            line = lines[anchor_idx]
            idx = line.lower().find(anchor.lower())
            after_text = line[idx + len(anchor):]
            if cap_pattern:
                m = re.search(cap_pattern, after_text)
                if m:
                    value = m.group(0).strip()
            else:
                value = after_text.strip().strip(":").strip()

        elif direction == "below":
            # Scan lines below anchor
            search_start = anchor_idx + 1 + skip
            search_end = min(len(lines), search_start + 10)
            for line in lines[search_start:search_end]:
                candidate = line.strip()
                if not candidate:
                    continue
                if cap_pattern:
                    m = re.search(cap_pattern, candidate)
                    if m:
                        value = m.group(0).strip()
                        break
                else:
                    value = candidate
                    break

        if value:
            if transform:
                value = self._transform(value, transform)
            self._set_value(rule, result, value)
            logger.debug(f"positional -> {rule.get('key') or target} = {value!r}")

    def _apply_section(self, rule, text, _tables, result):
        """
        Extract all text between two section markers.

        YAML spec:
            type: section
            start_marker: "III. BORROWER"
            end_marker: "IV. EMPLOYMENT"
            capture_pattern: '...'   # optional regex within the section
            target_path: "..."
        """
        start_marker = rule.get("start_marker", "")
        end_marker = rule.get("end_marker", "")
        cap_pattern = rule.get("capture_pattern")
        target = rule["target_path"]
        transform = rule.get("transform")

        lines = text.split("\n")
        start_idx = None
        end_idx = len(lines)

        for i, line in enumerate(lines):
            if start_marker.lower() in line.lower():
                start_idx = i
            elif start_idx is not None and end_marker and end_marker.lower() in line.lower():
                end_idx = i
                break

        if start_idx is None:
            logger.debug(f"section '{rule.get('id')}': start '{start_marker}' not found")
            return

        section_text = "\n".join(lines[start_idx:end_idx])

        if cap_pattern:
            m = re.search(cap_pattern, section_text, re.DOTALL)
            if m:
                value = m.group(1).strip() if m.lastindex else m.group(0).strip()
                if transform:
                    value = self._transform(value, transform)
                self._set_value(rule, result, value)
                logger.debug(f"section -> {rule.get('key') or target} = {value!r}")
        else:
            self._set_value(rule, result, section_text.strip())

    # ================================================================
    #  COMMON RULES  (both modes)
    # ================================================================

    def _apply_regex(self, rule, text, _tables, result):
        pattern = rule["pattern"]
        flags = 0
        for flag_name in rule.get("flags", []):
            flags |= getattr(re, flag_name, 0)

        match = re.search(pattern, text, flags)
        if not match:
            return

        if "group" in rule:
            group_idx = rule["group"]
            value = match.group(group_idx).strip()
            transform = rule.get("transform")
            if transform:
                value = self._transform(value, transform)
            self._set_value(rule, result, value)
            logger.debug(f"regex -> {rule.get('key') or rule.get('target_path')} = {value!r}")
            return

        # Multi-group regex: uses "groups" dict {group_id: target_path}
        # and optional "groups_keys" dict {group_id: flat_key} for flat mode
        groups = rule.get("groups", {})
        groups_keys = rule.get("groups_keys", {})
        for gid_str, target in groups.items():
            gid = int(gid_str)
            try:
                value = match.group(gid).strip()
                if self._output_mode == "flat":
                    flat_key = groups_keys.get(gid_str)
                    if flat_key:
                        result[flat_key] = value
                    elif "key" in rule:
                        result[f"{rule['key']}_{gid}"] = value
                    else:
                        _set_nested(result, target, value)
                else:
                    _set_nested(result, target, value)
                logger.debug(f"regex -> {groups_keys.get(gid_str) or target} = {value!r}")
            except IndexError:
                pass

    def _apply_static(self, rule, _text, _tables, result):
        self._set_value(rule, result, rule["value"])

    def _apply_computed(self, rule, _text, _tables, result):
        if self._output_mode == "flat":
            # In flat mode, use source_key to look up from flat dict
            source_key = rule.get("source_key")
            if source_key and source_key in result:
                source_val = result[source_key]
            else:
                # Fallback to nested lookup for backward compatibility
                source_val = _get_nested(result, rule["source_path"])
        else:
            source_val = _get_nested(result, rule["source_path"])
        if source_val is not None:
            self._set_value(rule, result, source_val)
            logger.debug(f"computed -> {rule.get('key') or rule.get('target_path')} = {source_val!r}")

    # ================================================================
    #  DISPATCH TABLE
    # ================================================================

    _DISPATCH: Dict[str, Any] = {}  # populated after class body

    # ================================================================
    #  TABLE HELPERS  (Mode A)
    # ================================================================

    def _build_column_index(self, table):
        best_row = table[0] if table else []
        best_score = -1
        for row in table[:min(3, len(table))]:
            text_cells = sum(
                1 for c in row
                if c.strip() and not re.match(r"^[\$\d,.\-]+$", c.strip())
            )
            if text_cells > best_score:
                best_score = text_cells
                best_row = row
        index = {}
        for i, cell in enumerate(best_row):
            clean = cell.strip().upper()
            clean = re.sub(r"[-]+", "", clean).strip()
            if clean:
                index[clean] = i
        return index

    def _find_row_by_label(self, table, label):
        label_upper = label.upper()
        for row in table:
            for cell in row:
                if cell.strip().upper() == label_upper:
                    return row
        return None

    def _find_data_start(self, table):
        for i, row in enumerate(table):
            for cell in row:
                stripped = cell.strip()
                if re.match(r"^[\d,]+\.?\d*$", stripped):
                    return i
                if re.match(r"^\$?[\d,]+\.?\d*$", stripped):
                    return i
        return 1 if len(table) > 1 else 0

    # ================================================================
    #  TRANSFORMS
    # ================================================================

    def _transform(self, value: str, transform_name: str) -> Any:
        if transform_name == "annual_to_monthly":
            amount = _clean_currency(value)
            if amount is not None:
                return round(amount / 12, 2)
            return value
        if transform_name == "to_float":
            return _clean_currency(value)
        if transform_name == "to_int":
            try:
                return int(re.sub(r"[^\d]", "", value))
            except ValueError:
                return value
        if transform_name == "strip_ocr_noise":
            # Remove common OCR artifacts while keeping alphanumeric + basic punct
            return re.sub(r"[^A-Za-z0-9\s,.\-/()$%#@&']", "", value).strip()
        return value

    # ================================================================
    #  UTILITIES
    # ================================================================

    @staticmethod
    def _count_fields(d: Any, _depth: int = 0) -> int:
        if isinstance(d, dict):
            return sum(RuleEngine._count_fields(v, _depth + 1) for v in d.values())
        if isinstance(d, list):
            return sum(RuleEngine._count_fields(v, _depth + 1) for v in d)
        return 1 if d is not None else 0


# --- Populate dispatch table after class body ---
RuleEngine._DISPATCH = {
    # Mode A — Markdown
    "heading":     RuleEngine._apply_heading,
    "key_value":   RuleEngine._apply_key_value,
    "table":       RuleEngine._apply_table,
    # Mode B — OCR / Plain text
    "checkbox":    RuleEngine._apply_checkbox,
    "positional":  RuleEngine._apply_positional,
    "section":     RuleEngine._apply_section,
    # Common
    "regex":       RuleEngine._apply_regex,
    "static":      RuleEngine._apply_static,
    "computed":    RuleEngine._apply_computed,
}


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------

def extract_with_rules(
    markdown: str,
    document_type: str,
    schema: Optional[dict] = None,
    output_mode: str = "nested",
) -> Dict[str, Any]:
    """Deterministic extraction entry-point."""
    engine = RuleEngine()
    return engine.extract(markdown, document_type, output_mode=output_mode)
