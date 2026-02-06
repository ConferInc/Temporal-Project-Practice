"""
Structure Extractor Tool
Converts Markdown documents into structured Key-Value JSON using LLM.
"""

import os
import json
from openai import OpenAI

from utils.logging import logger
from tools.prompts import CANONICAL_EXTRACTION_PROMPT
from tools.urla_prompts import URLA_EXTRACTION_PROMPT
from dotenv import load_dotenv
load_dotenv()



def extract_canonical_structure(doc_data: dict, schema: dict, document_type: str = "Unknown", model: str = "gpt-5.1") -> dict:
    """
    Extract data directly into Canonical Schema format using LLM.
    
    Args:
        doc_data: Dictionary containing document data (from Dockling)
        schema: Target canonical schema
        document_type: Type of document
        model: OpenAI model to use
    
    Returns:
        Dictionary containing the canonical output
    """
    try:

        logger.info(f"Starting canonical extraction for {document_type}")
        
        # 1. Prepare inputs
        doc_data_str = json.dumps(doc_data, indent=2, ensure_ascii=False)
        # Limit doc data size if needed to fit context window
        if len(doc_data_str) > 100000:
             logger.warning(f"Document data too large ({len(doc_data_str)} chars). Truncating...")
             doc_data_str = doc_data_str[:100000] + "... (truncated)"
             
        schema_str = json.dumps(schema, indent=2)
        
        # 2. Construct the prompt
        schema_str = json.dumps(schema, indent=2)
        
        # 2. Construct the prompt
        if document_type == "URLA" or document_type == "URLA (Form 1003)":
             prompt = URLA_EXTRACTION_PROMPT.format(
                doc_data=doc_data_str,
                schema=schema_str
            )
        else:
            prompt = CANONICAL_EXTRACTION_PROMPT.format(
                document_type=document_type,
                doc_data=doc_data_str,
                schema=schema_str
            )
        
        # 3. Call OpenAI API
        logger.info(f"Calling OpenAI API with model {model}")
        
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_BASE_URL")
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a data mapping expert. Output valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # 4. Parse the response
        generated_content = response.choices[0].message.content
        logger.info("Received response from OpenAI")
        
        # Clean up response
        if generated_content.startswith("```"):
             generated_content = generated_content.strip("`").replace("json", "").strip()

        canonical_data = json.loads(generated_content)
        
        return canonical_data

    except Exception as e:
        logger.error(f"Canonical extraction failed: {e}")
        raise
