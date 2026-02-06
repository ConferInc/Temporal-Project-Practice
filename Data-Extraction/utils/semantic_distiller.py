import json
from typing import Any, Dict, List

# ---------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------

# Keys that are pure layout / rendering noise
REMOVE_KEYS = {
    "bbox",
    "polygon",
    "font",
    "span",
    "char_index",
    "rotation",
    "confidence_char",
    "render_info",
    "color",
    "page_number",
    "reading_order",
    "style",
}

# Known table headers we care about (mortgage-focused)
TABLE_KEYWORDS = {
    "transaction",
    "deposit",
    "withdrawal",
    "date",
    "amount",
    "balance",
    "description",
    "employer",
    "income",
    "liability",
}

# Section keywords to keep (mortgage semantics)
SECTION_KEYWORDS = {
    "borrower",
    "co-borrower",
    "applicant",
    "employment",
    "income",
    "asset",
    "bank",
    "liability",
    "property",
    "collateral",
    "loan",
    "mortgage",
    "declaration",
    "identity",
    "citizenship",
    "residency",
}

# ---------------------------------------------------------
# CORE DISTILLER
# ---------------------------------------------------------

def is_noise_key(key: str) -> bool:
    return key.lower() in REMOVE_KEYS


def is_empty(value: Any) -> bool:
    return value in (None, "", [], {})


def distill(obj: Any) -> Any:
    """
    Recursively remove noise while preserving semantic structure.
    """
    if isinstance(obj, dict):
        clean = {}
        for k, v in obj.items():
            if is_noise_key(k):
                continue
            distilled_value = distill(v)
            if not is_empty(distilled_value):
                clean[k] = distilled_value
        return clean

    elif isinstance(obj, list):
        return [distill(i) for i in obj if not is_empty(distill(i))]

    return obj


# ---------------------------------------------------------
# TEXT COLLAPSING
# ---------------------------------------------------------

def collapse_text_nodes(node: Dict) -> str:
    """
    Collapses nested token/line structures into plain text.
    """
    text_fragments = []

    def walk(n):
        if isinstance(n, dict):
            if "text" in n and isinstance(n["text"], str):
                text_fragments.append(n["text"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for i in n:
                walk(i)

    walk(node)
    return " ".join(text_fragments).strip()


# ---------------------------------------------------------
# TABLE EXTRACTION
# ---------------------------------------------------------

def extract_tables(node: Any) -> List[Dict]:
    """
    Extracts table-like structures and converts them into row-based JSON.
    """
    tables = []

    if isinstance(node, dict):
        if "rows" in node and isinstance(node["rows"], list):
            structured_rows = []
            for row in node["rows"]:
                row_data = {}
                for cell in row.get("cells", []):
                    header = cell.get("header", "").lower()
                    value = cell.get("text")
                    if any(k in header for k in TABLE_KEYWORDS):
                        row_data[header] = value
                if row_data:
                    structured_rows.append(row_data)

            if structured_rows:
                tables.append(structured_rows)

        for v in node.values():
            tables.extend(extract_tables(v))

    elif isinstance(node, list):
        for i in node:
            tables.extend(extract_tables(i))

    return tables


# ---------------------------------------------------------
# SECTION FILTERING
# ---------------------------------------------------------

def is_relevant_section(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in SECTION_KEYWORDS)


def extract_semantic_sections(doc: Dict) -> Dict:
    """
    Keeps only mortgage-relevant semantic sections.
    """
    sections = {}

    for key, value in doc.items():
        collapsed_text = collapse_text_nodes(value)
        if is_relevant_section(collapsed_text):
            sections[key] = {
                "text": collapsed_text,
                "tables": extract_tables(value)
            }

    return sections


def process_dockling_data(doc_data: Dict) -> Dict:
    """
    Process in-memory Dockling data: Extract ONLY essential information in token-efficient format.
    
    Strategy:
    1. Extract all text content (flatten nested structures)
    2. Extract key-value pairs
    3. Extract table data in simple row format
    4. Remove ALL redundant structure, metadata, and empty values
    
    Goal: Minimize tokens while preserving ALL semantic content.
    """
    
    result = {
        "document_info": {},
        "text_content": [],
        "key_value_pairs": [],
        "tables": []
    }
   
    # Extract document metadata
    if "name" in doc_data:
        result["document_info"]["name"] = doc_data["name"]
    
    # Helper: Recursively extract all text
    def extract_all_text(obj: Any, parent_label: str = "") -> List[str]:
        texts = []
        
        if isinstance(obj, dict):
            # Get label/type for context
            label = obj.get("label", obj.get("name", parent_label))
            
            # Extract text field
            if "text" in obj and isinstance(obj["text"], str):
                text_val = obj["text"].strip()
                if text_val and len(text_val) > 1:  # Skip single chars
                    texts.append(text_val)
            
            # Recurse into children
            for key, value in obj.items():
                if key not in ["text", "bbox", "prov", "font", "polygon"]:
                    texts.extend(extract_all_text(value, label))
        
        elif isinstance(obj, list):
            for item in obj:
                texts.extend(extract_all_text(item, parent_label))
        
        return texts
    
    # Helper: Extract key-value pairs
    def extract_key_values(obj: Any) -> List[Dict]:
        pairs = []
        
        if isinstance(obj, dict):
            # Check for key_value_items structure
            if "key_value_items" in obj:
                for item in obj["key_value_items"]:
                    if isinstance(item, dict):
                        key_text = ""
                        val_text = ""
                        
                        # Extract key
                        if "key" in item:
                            key_text = collapse_text_nodes(item["key"])
                        
                        # Extract value
                        if "value" in item:
                            val_text = collapse_text_nodes(item["value"])
                        
                        if key_text and val_text:
                            pairs.append({"key": key_text, "value": val_text})
            
            # Recurse
            for value in obj.values():
                pairs.extend(extract_key_values(value))
        
        elif isinstance(obj, list):
            for item in obj:
                pairs.extend(extract_key_values(item))
        
        return pairs
    
    # Helper: Extract tables in simple format
    def extract_simple_tables(obj: Any) -> List[Dict]:
        tables = []
        
        if isinstance(obj, dict):
            # Check for table structure
            if "data" in obj and isinstance(obj["data"], dict):
                table_data = obj["data"]
                if "grid" in table_data:
                    # Extract grid as simple rows
                    grid = table_data["grid"]
                    simple_table = []
                    
                    for row in grid:
                        if isinstance(row, list):
                            row_data = []
                            for cell in row:
                                cell_text = collapse_text_nodes(cell) if isinstance(cell, dict) else str(cell)
                                if cell_text.strip():
                                    row_data.append(cell_text.strip())
                            if row_data:
                                simple_table.append(row_data)
                    
                    if simple_table:
                        tables.append({"rows": simple_table})
            
            # Recurse
            for value in obj.values():
                tables.extend(extract_simple_tables(value))
        
        elif isinstance(obj, list):
            for item in obj:
                tables.extend(extract_simple_tables(item))
        
        return tables
    
    # Extract all text content
    all_texts = extract_all_text(doc_data)
    # Deduplicate while preserving order
    seen = set()
    for text in all_texts:
        if text not in seen and len(text) > 2:  # Skip very short strings
            result["text_content"].append(text)
            seen.add(text)
    
    # Extract key-value pairs
    result["key_value_pairs"] = extract_key_values(doc_data)
    
    # Extract tables
    result["tables"] = extract_simple_tables(doc_data)
    
    # Remove empty sections
    if not result["key_value_pairs"]:
        del result["key_value_pairs"]
    if not result["tables"]:
        del result["tables"]
    if not result["document_info"]:
        del result["document_info"]
    
    return result



# ---------------------------------------------------------
# MAIN ENTRY
# ---------------------------------------------------------

def distill_docling_json(
    input_path: str,
    output_path: str
) -> None:
    """
    End-to-end semantic distillation.
    """

    with open(input_path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    # Step 1: Remove layout noise
    cleaned = distill(raw)

    # Step 2: Extract mortgage-relevant sections
    semantic_output = extract_semantic_sections(cleaned)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(semantic_output, f, indent=2)

    print("✅ Semantic distillation completed.")
    print(f"📉 Size reduced significantly: {output_path}")


# ---------------------------------------------------------
# CLI USAGE
# ---------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python semantic_distiller.py <input.json> <output.json>")
        sys.exit(1)

    distill_docling_json(sys.argv[1], sys.argv[2])
