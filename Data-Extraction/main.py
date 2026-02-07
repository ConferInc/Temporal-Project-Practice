#!/usr/bin/env python
"""
Data-Extraction Pipeline — Phase 1 CLI

Flow:
  Input → ensure_pdf() → split_document_blob() → Loop[unified_extract] → JSON

Artifacts are saved in output/{stem}/:
  1_raw.txt          – raw OCR or markdown
  1b_merged_flat.json– merged flat data (multi-doc only)
  2_canonical.json   – canonical model
  3_mismo.xml        – MISMO 3.4 XML
  report.md          – run summary
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Windows console encoding fix (must run before argparse for help text)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(
        description="Run the document extraction pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input paystub.pdf
  python main.py --input photo.jpg                     (auto-converts to PDF)
  python main.py --input scan.heic                     (HEIC -> PDF)
  python main.py --input mega_loan_file.pdf             (auto-splits)
  python main.py --input paystub.pdf --mode flat
  python main.py --multi --input w2.pdf --input paystub.pdf
        """
    )
    parser.add_argument("--input", "-i", required=True, action="append",
                        help="Path to input file(s). Use multiple --input for multi-doc mode.")
    parser.add_argument("--output-dir", "-o", default="./output",
                        help="Base output directory (default: ./output)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    parser.add_argument("--mode", choices=["nested", "flat"], default="nested",
                        help="Extraction mode: 'nested' (legacy) or 'flat' (two-stage)")
    parser.add_argument("--multi", action="store_true",
                        help="Multi-document mode: merge extractions from all --input files")
    parser.add_argument("--no-split", action="store_true",
                        help="Disable automatic mega-PDF splitting")
    args = parser.parse_args()

    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    # =====================================================================
    # PHASE 1a: Image Conversion  (ensure everything is PDF)
    # =====================================================================
    from src.preprocessing.converter import ensure_pdf, cleanup_temp

    raw_paths = [Path(p) for p in args.input]
    for rp in raw_paths:
        if not rp.exists():
            print(f"Error: Input file not found: {rp}")
            sys.exit(1)

    print("=" * 60)
    print("  DATA EXTRACTION PIPELINE  (Phase 1)")
    print("=" * 60)

    pdf_paths: list[str] = []
    for rp in raw_paths:
        print(f"  Converting: {rp.name} ... ", end="")
        pdf_path = ensure_pdf(str(rp))
        pdf_paths.append(pdf_path)
        if str(Path(pdf_path).resolve()) == str(rp.resolve()):
            print("PDF (passthrough)")
        else:
            print(f"→ {Path(pdf_path).name}")

    # =====================================================================
    # PHASE 1b: Document Splitting  (always attempt on multi-page PDFs)
    # =====================================================================
    from src.preprocessing.splitter import (
        split_document_blob,
        cleanup_chunks,
    )
    from pypdf import PdfReader

    chunk_paths: list[str] = []
    did_split = False

    if not args.no_split:
        for pp in pdf_paths:
            page_count = len(PdfReader(pp).pages)
            if page_count > 1:
                # Always attempt to split multi-page PDFs
                print(f"\n  Scanning {Path(pp).name} ({page_count} pages) for document boundaries...")
                sub_chunks = split_document_blob(pp)
                if len(sub_chunks) > 1:
                    did_split = True
                    chunk_paths.extend(sub_chunks)
                else:
                    # Splitter found only 1 document type — use original
                    cleanup_chunks(sub_chunks)
                    chunk_paths.append(pp)
                    print(f"  Single document type detected, no split needed.")
            else:
                chunk_paths.append(pp)
    else:
        chunk_paths = pdf_paths

    # Force multi mode if we have >1 chunk
    if len(chunk_paths) > 1:
        args.multi = True
    elif len(chunk_paths) == 1 and args.multi:
        print("  Warning: --multi with 1 chunk. Running single-doc mode.")
        args.multi = False

    # Structured output dir
    if args.multi:
        stem = "multi_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    else:
        stem = Path(chunk_paths[0]).stem
    run_dir = Path(args.output_dir) / stem
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.multi:
        print(f"\n  Mode:   Multi-document merge ({len(chunk_paths)} chunks)")
    else:
        print(f"\n  Mode:   {args.mode}")
    print(f"  Output: {run_dir.absolute()}")
    print()

    from dotenv import load_dotenv
    load_dotenv()

    t_start = datetime.now()
    report_lines = [
        f"# Extraction Report",
        f"**File(s):** `{', '.join(Path(p).name for p in chunk_paths)}`",
        f"**Run:** {t_start.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Mode:** {'multi-document' if args.multi else args.mode}",
        f"**Auto-split:** {'Yes' if did_split else 'No'}",
        "",
    ]

    try:
        # =================================================================
        # STEP 2: Extract
        # =================================================================
        from src.logic.unified_extraction import unified_extract, unified_extract_multi
        from src.mapping.mismo_emitter import emit_mismo_xml

        if args.multi:
            print(f"  [1/4] Processing {len(chunk_paths)} documents...")
            multi_result = unified_extract_multi(chunk_paths)

            canonical_data = multi_result.get("canonical_data", {})
            classifications = multi_result.get("classifications", [])
            doc_type = "Multi-document merge"
            confidence = 1.0
            tool_used = "multi"
            raw_summary = f"Merged {len(chunk_paths)} documents"

            flat_path = run_dir / "1b_merged_flat.json"
            flat_path.write_text(
                json.dumps(multi_result.get("merged_flat", {}), indent=2,
                           ensure_ascii=False, default=str),
                encoding="utf-8",
            )

            result = {
                "classification": classifications[0] if classifications else {},
                "canonical_data": canonical_data,
                "raw_extraction_summary": raw_summary,
            }
        else:
            print("  [1/4] Classifying & extracting raw content...")
            result = unified_extract(
                chunk_paths[0],
                output_mode=args.mode,
            )

        if not args.multi:
            classification = result.get("classification", {})
            doc_type = classification.get("document_category", "Unknown")
            confidence = classification.get("confidence", 0)
            tool_used = classification.get("recommended_tool", "Unknown")
            raw_summary = result.get("raw_extraction_summary", "")
            canonical_data = result.get("canonical_data", {})

        report_lines += [
            "## Classification",
            f"- **Document Type:** {doc_type}",
            f"- **Confidence:** {confidence:.0%}",
            f"- **Extraction Tool:** {tool_used}",
            "",
        ]

        # --- Save raw ---
        print("  [2/4] Saving raw extraction...")
        raw_path = run_dir / "1_raw.txt"
        raw_path.write_text(raw_summary, encoding="utf-8")

        # --- Save canonical ---
        print("  [3/4] Saving canonical model...")
        canonical_path = run_dir / "2_canonical.json"
        canonical_path.write_text(
            json.dumps(canonical_data, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

        field_count = _count_fields(canonical_data)
        report_lines += [
            "## Extraction Results",
            f"- **Fields Extracted:** {field_count}",
            "",
        ]

        # --- MISMO XML ---
        print("  [4/4] Generating MISMO 3.4 XML...")
        mismo_xml = emit_mismo_xml(canonical_data)

        xml_path = run_dir / "3_mismo.xml"
        if mismo_xml:
            xml_path.write_text(mismo_xml, encoding="utf-8")
            report_lines.append(f"- **MISMO XML:** Generated ({len(mismo_xml)} chars)")
        else:
            xml_path.write_text("<!-- No data to emit -->", encoding="utf-8")
            report_lines.append("- **MISMO XML:** Empty (no deal data)")
        report_lines.append("")

        # --- Critical fields ---
        critical_paths = [
            ("Borrower Name",  "deal.parties.0.individual.full_name"),
            ("Borrower SSN",   "deal.parties.0.individual.ssn"),
            ("Loan Purpose",   "deal.transaction_information.loan_purpose.value"),
            ("Property Addr",  "deal.collateral.subject_property.address"),
            ("Loan Amount",    "deal.disclosures_and_closing.promissory_note.principal_amount"),
        ]

        missing = []
        present = []
        for label, path in critical_paths:
            val = _deep_get(canonical_data, path)
            if val:
                present.append(f"- [x] **{label}:** `{val}`")
            else:
                missing.append(f"- [ ] **{label}:** MISSING")

        report_lines += ["## Critical Fields"]
        report_lines += present + missing
        report_lines.append("")

        if missing:
            report_lines += [
                "## Warnings",
                f"- {len(missing)} critical field(s) missing.",
                "",
            ]

        # --- Finalize ---
        t_end = datetime.now()
        elapsed = (t_end - t_start).total_seconds()
        report_lines += [
            "## Performance",
            f"- **Elapsed:** {elapsed:.2f}s",
            f"- **Engine:** Deterministic Rule Engine (zero LLM)",
            "",
        ]

        report_path = run_dir / "report.md"
        report_path.write_text("\n".join(report_lines), encoding="utf-8")

        # --- Console summary ---
        print()
        print("=" * 60)
        print("  PIPELINE COMPLETE")
        print("=" * 60)
        print(f"  Classification:   {doc_type}")
        print(f"  Confidence:       {confidence:.0%}")
        print(f"  Extraction Tool:  {tool_used}")
        print(f"  Canonical Fields: {field_count}")
        print(f"  Missing Critical: {len(missing)}")
        print(f"  Elapsed:          {elapsed:.2f}s")
        if did_split:
            print(f"  Auto-Split:       {len(chunk_paths)} chunks")
        print()
        print(f"  Artifacts:")
        print(f"    {raw_path}")
        print(f"    {canonical_path}")
        print(f"    {xml_path}")
        print(f"    {report_path}")
        print("=" * 60)

    except Exception as e:
        print(f"Pipeline failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup temp files from converter and splitter
        cleanup_temp()
        if did_split:
            cleanup_chunks(chunk_paths)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _count_fields(d, depth=0):
    """Count leaf values in a nested structure."""
    if isinstance(d, dict):
        return sum(_count_fields(v, depth + 1) for v in d.values())
    if isinstance(d, list):
        return sum(_count_fields(v, depth + 1) for v in d)
    return 1 if d is not None else 0


def _deep_get(data, dotted_path):
    """Get a value from nested dict using dot notation."""
    parts = dotted_path.split(".")
    current = data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list):
            try:
                current = current[int(part)]
            except (ValueError, IndexError):
                return None
        else:
            return None
    return current


if __name__ == "__main__":
    main()
