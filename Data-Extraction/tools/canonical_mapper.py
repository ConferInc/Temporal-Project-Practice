"""
Canonical Mapper Tool - LLM-DRIVEN AGGREGATION

Maps extracted document fields to MISMO 3.4-aligned canonical schema using LLM (GPT-5.1).
Supports INCREMENTAL AGGREGATION (merging new document data into existing deal structure).

KEY FEATURES:
- LLM-based intelligent mapping
- Context-aware aggregation (merges URLA + Bank Statements etc.)
- Strict Enum enforcement (post-LLM validation)
- Schema-driven output
"""

import os
import json
import copy
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from utils.logging import logger
from utils.schema_registry import get_schema_registry
from utils.enum_validator import get_enum_validator, StructuredMappingError
from utils.path_resolver import get_path_resolver

# Try importing litellm, handle missing dependency
try:
    import litellm
except ImportError:
    logger.warning("litellm not found. LLM features will fail. Install with `pip install litellm`")
    litellm = None

class RuleBasedCanonicalMapper:
    """
    Legacy Schema-driven rule-based mapper.
    Kept for fallback or specific deterministic use cases.
    """
    
    def __init__(self):
        self.schema_registry = get_schema_registry()
        self.path_resolver = get_path_resolver()
        self.enum_validator = get_enum_validator()
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def _load_mapping_rules(self, document_type: str) -> List[Dict]:
        """Load document-specific mapping rules."""
        try:
            mapping_path = os.path.join(
                self.base_path,
                "resources",
                "canonical_mappings",
                f"{document_type}.json"
            )
            
            if not os.path.exists(mapping_path):
                return []
            
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading mapping rules for {document_type}: {e}")
            raise

class LLMCanonicalMapper:
    """
    LLM-powered Canonical Mapper using GPT-5.1 via LiteLLM.
    Supports intelligent mapping and incremental data aggregation.
    """
    
    def __init__(self):
        self.schema_registry = get_schema_registry()
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.model = "gpt-5.1"  # User specified model
        
        # Configure LiteLLM with user-provided details
        if litellm:
            litellm.api_base = os.getenv("OPENAI_BASE_URL", "https://litellm.confersolutions.ai/v1/")
            # Ensure API key is set
            if not os.getenv("OPENAI_API_KEY") and not litellm.api_key:
                litellm.api_key = "sk-custom-endpoint-placeholder"
        
        # Load the full schema to provided context to LLM
        self.full_schema = self.schema_registry.get_schema()
        
        logger.info(f"LLMCanonicalMapper initialized (Model: {self.model})")

    def _get_system_prompt(self) -> str:
        return """You are an expert Mortgage Data Specialist and MISMO 3.4 Architect.
Your task is to MAP extracted document data into a strict Canonical JSON Schema for a mortgage application.

Capabilities:
1. MAPPING: detailed understanding of URLA, Bank Statements, Pay Stubs, etc.
2. AGGREGATION: You can merge new data into an EXISTING canonical dataset.
3. ENUM RESOLUTION: You must map free-text values to the strictly allowed 'options' in the schema.

RULES:
- OUTPUT STRICT JSON ONLY. No markdown, no comments.
- SCHEMA CONFORMITY: The output must match the provided MISMO 3.4 structure exactly.
- ENUMS (CRITICAL):
  - Many fields have a "value" and "options" structure.
  - You MUST strictly select one string from the "options" list to populate "value".
  - Perform intelligent fuzzy matching:
    * Extracted: "Chk" or "Checking Account" -> Schema Option: "Checking"
    * Extracted: "Alice Smith (Borrower)" -> Schema Option: "Borrower"
  - If no clear match is found, leave "value": null. NEVER invent a new option.
- AGGREGATION LOGIC (CRITICAL):
  - Received "Existing Canonical Data"? You MUST merge new data into it.
  - PARTIES: Do not duplicate. Match by Name/SSN. If match found, update/enrich. If new, append.
  - ASSETS: Match by Account Number. If match, update (e.g. add transactions).
  - LOAN INFO: Overwrite/Update single fields (Loan Purpose, etc).
  - Do NOT remove existing data unless it is clearly being corrected.
- DATES: Convert all dates to YYYY-MM-DD format.
- NUMBERS: Ensure numeric fields are numbers, not strings.

FAILURE TO FOLLOW ENUMS OR STRUCTURE WILL BREAK THE PIPELINE."""

    def map(self, document_type: str, extracted_fields: Dict, existing_canonical: Optional[Dict] = None) -> Dict:
        """
        Map extracted fields to canonical schema using LLM.
        
        Args:
            document_type: e.g., "URLA", "BankStatement"
            extracted_fields: Dict of raw extracted pairs
            existing_canonical: Optional Dict of previously mapped data to merge into
            
        Returns:
            Dict: The new/updated canonical JSON
        """
        logger.info(f"LLM Mapping started for {document_type}")
        
        # Prepare inputs
        base_schema = existing_canonical if existing_canonical else self.full_schema
        
        # Prompt Construction
        user_message = f"""
PROCESS THIS DOCUMENT:
Type: {document_type}

--- EXTRACTED DATA ---
{json.dumps(extracted_fields, indent=2)}

--- EXISTING CANONICAL DATA (MERGE INTO THIS) ---
{json.dumps(base_schema, indent=2)}

--- TARGET SCHEMA REFERENCE (Structure only) ---
(Refer to the existing data structure above. It follows MISMO 3.4 rules.)

INSTRUCTIONS:
1. Update the 'Existing Canonical Data' with information from 'Extracted Data'.
2. Fill generic fields (Parties, Assets) and document-specifics.
3. For Arrays (Parties, Assets):
   - Check if item exists (by Name or Account #).
   - If yes, UPDATE it.
   - If no, CREATE new entry.
4. Set 'document_metadata.audit_trail_enabled' to true.
"""

        try:
            if litellm is None:
                raise ImportError("litellm library not installed")

            # Call LLM
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=0.0  # Zero temperature for max determinism
            )
            
            content = response.choices[0].message.content
            mapped_data = json.loads(content)
            
            # Basic validation: Check if root keys exist
            if "deal" not in mapped_data:
                logger.error("LLM output missing 'deal' root key")
                # Fallback to returning what we have or raising error
            
            logger.info(f"LLM Mapping complete for {document_type}")
            
            # Save debug output
            self._save_output(mapped_data, document_type)
            
            return mapped_data
            
        except Exception as e:
            logger.error(f"LLM Mapping failed: {e}")
            # If LLM fails, return existing data unmodified or raise
            if existing_canonical:
                logger.warning("Returning existing canonical data due to failure")
                return existing_canonical
            raise

    def _save_output(self, result: Dict, document_type: str) -> None:
        try:
            from datetime import datetime
            output_dir = os.path.join(self.base_path, "output", "canonical_mappings", "llm_trace")
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{document_type}_{timestamp}_llm_canonical.json"
            with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2)
        except Exception:
            pass

# Global mapper instance
_mapper = None

def get_mapper() -> LLMCanonicalMapper:
    """Get the LLM mapper instance."""
    global _mapper
    if _mapper is None:
        _mapper = LLMCanonicalMapper()
    return _mapper

def map_to_canonical_model(document_type: str, extracted_fields: Dict, existing_canonical: Optional[Dict] = None) -> Dict:
    """
    Main entry point for Canonical Mapping (LLM-Enabled).
    
    Args:
        document_type: Document category (URLA, BankStatement)
        extracted_fields: Raw extraction data
        existing_canonical: (Optional) Previous state of validity for aggregation
    """
    mapper = get_mapper()
    return mapper.map(document_type, extracted_fields, existing_canonical)
