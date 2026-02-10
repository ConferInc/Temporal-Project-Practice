#!/usr/bin/env python
"""
Data-Extraction Pipeline — Production CLI

Flow:
  Input → ensure_pdf() → split_document_blob()
    → Extract (Rules) → Assemble (Canonical) → Validate → Transform (Relational)
    → Output JSONs

Artifacts are saved in output/{stem}/:
  1_raw.txt                – raw OCR or markdown
  1b_merged_flat.json      – merged flat data (multi-doc only)
  2_canonical.json         – canonical model (Nested View)
  3_relational_payload.json– Supabase table payload (Database View)
  report.md                – run summary
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
    print("  DATA EXTRACTION PIPELINE")
    print("=" * 60)

    pdf_paths: list[str] = []
    image_source_paths: set[str] = set()  # tracks files converted from images
    for rp in raw_paths:
        print(f"  Converting: {rp.name} ... ", end="")
        pdf_path = ensure_pdf(str(rp))
        pdf_paths.append(pdf_path)
        if str(Path(pdf_path).resolve()) == str(rp.resolve()):
            print("PDF (passthrough)")
        else:
            image_source_paths.add(pdf_path)
            print(f"→ {Path(pdf_path).name} (image source → OCR)")

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
        # STEP 1: Extract & Assemble
        # =================================================================
        from src.logic.unified_extraction import unified_extract, unified_extract_multi
        from src.logic.validator import DataValidator
        from src.mapping.relational_transformer import RelationalTransformer

        _MIN_TEXT_LENGTH = 50  # fallback threshold for scanned PDFs

        if args.multi:
            print(f"  [1/5] Processing {len(chunk_paths)} documents...")
            multi_result = unified_extract_multi(
                chunk_paths,
                force_ocr_paths=image_source_paths,
            )

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
            is_image_source = chunk_paths[0] in image_source_paths
            print(f"  [1/5] Classifying & extracting raw content"
                  f"{' (OCR — image source)' if is_image_source else ''}...")
            result = unified_extract(
                chunk_paths[0],
                output_mode=args.mode,
                force_ocr=is_image_source,
            )

            # Fallback: if Dockling returned too little text, retry with OCR
            if (not is_image_source
                    and result.get("_raw_text_length", 0) < _MIN_TEXT_LENGTH):
                raw_len = result.get("_raw_text_length", 0)
                print(f"  [WARN] Low text yield ({raw_len} chars), "
                      f"retrying with OCR...")
                result = unified_extract(
                    chunk_paths[0],
                    output_mode=args.mode,
                    force_ocr=True,
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

        # =================================================================
        # STEP 2: Save raw extraction
        # =================================================================
        print("  [2/5] Saving raw extraction & canonical...")
        raw_path = run_dir / "1_raw.txt"
        # Save full raw text if available, otherwise use summary
        raw_full_text = result.get("raw_extraction_full", raw_summary)
        raw_path.write_text(raw_full_text, encoding="utf-8")

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

        # =================================================================
        # STEP 3: Validate canonical data
        # =================================================================
        print("  [3/5] Validating data quality...")
        validator = DataValidator()
        canonical_data, validation_errors = validator.validate(canonical_data)

        if validation_errors:
            print()
            print(f"  [WARN] Validation Issues Found: {len(validation_errors)}")
            for err in validation_errors:
                print(f"    - {err}")
            print()

            report_lines += ["## Validation Issues"]
            for err in validation_errors:
                report_lines.append(f"- {err}")
            report_lines.append("")
        else:
            print("  [PASS] All validation checks passed.")
            report_lines += [
                "## Validation",
                "- All checks passed.",
                "",
            ]

        # =================================================================
        # STEP 4: Relational Payload (Database View)
        # =================================================================
        print("  [4/5] Generating relational payload...")
        rt = RelationalTransformer()
        relational_payload = rt.transform(canonical_data)
        
        # Apply schema enforcement to ensure database compliance
        from src.mapping.schema_enforcer import SchemaEnforcer
        enforcer = SchemaEnforcer()
        relational_payload = enforcer.enforce(relational_payload)

        relational_path = run_dir / "3_relational_payload.json"
        relational_path.write_text(
            json.dumps(relational_payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        row_count = relational_payload.get("_metadata", {}).get("total_rows", 0)
        table_count = relational_payload.get("_metadata", {}).get("table_count", 0)
        report_lines += [
            "## Database Payload",
            f"- **Relational Payload:** {row_count} rows across {table_count} tables",
            "",
        ]

        # =================================================================
        # STEP 5: Finalize report
        # =================================================================
        print("  [5/5] Writing report...")
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
        print(f"  Validation:       {'PASS' if not validation_errors else f'{len(validation_errors)} issue(s)'}")
        print(f"  DB Payload:       {row_count} rows / {table_count} tables")
        print(f"  Elapsed:          {elapsed:.2f}s")
        if did_split:
            print(f"  Auto-Split:       {len(chunk_paths)} chunks")
        print()
        print(f"  Artifacts:")
        print(f"    {raw_path}")
        print(f"    {canonical_path}")
        print(f"    {relational_path}")
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


if __name__ == "__main__":
    main()
