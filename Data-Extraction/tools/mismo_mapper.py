"""
MISMO Mapper Tool
Converts Canonical Model v3 JSON -> MISMO v3.4 XML

Adheres to strict architectural rules:
- No LLM inference
- Table-driven mapping
- Deterministic output
"""

import json
import os
import re
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from utils.logging import logger

class MismoMapper:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.mapping_rules = self._load_mapping_rules()

    def _load_mapping_rules(self) -> List[Dict]:
        """Load mapping definitions from resources"""
        try:
            path = os.path.join(self.base_path, "resources", "mismo_mapping", "map_mismo_3_6.json")
            with open(path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            logger.info(f"✅ Loaded {len(rules)} MISMO mapping rules")
            return rules
        except Exception as e:
            logger.error(f"Failed to load MISMO mapping rules: {e}")
            raise

    def _get_value_at_path(self, data: Dict, path: str) -> Any:
        """
        Retrieve value from canonical data using dot notation with array indices.
        Example: parties[0].individual.firstName
        """
        try:
            # Handle array access like parties[0]
            # Regex to split identifiers and indices: parties[0] -> parts: parties, 0
            # Simple split by '.' first
            keys = path.split('.')
            current = data
            
            for key in keys:
                if '[' in key and ']' in key:
                    # Extract name and index
                    match = re.match(r"(\w+)\[(\d+)\]", key)
                    if not match:
                        return None
                    name, index = match.groups()
                    index = int(index)
                    
                    if name not in current or not isinstance(current[name], list):
                        return None
                    if index >= len(current[name]):
                        return None
                    
                    current = current[name][index]
                else:
                    if key not in current:
                        return None
                    current = current[key]
            
            return current
        except Exception:
            return None

    def _set_value_at_xpath(self, root: Dict, xpath: str, value: Any) -> None:
        """
        Set value in intermediate nested dict structure using pseudo-XPath.
        Handling arrays based on path indices [0].
        
        XPath: /MESSAGE/DEAL_SETS.../PARTY[0]/...
        """
        parts = xpath.strip('/').split('/')
        current = root
        
        for i, part in enumerate(parts[:-1]):
            # Check for array index in XPath part (e.g., PARTY[0])
            # Our mapping table gives implicit arrays (PARTY), but concrete paths have indices
            
            is_array = False
            index = 0
            clean_part = part
            
            if '[' in part and ']' in part:
                match = re.match(r"(\w+)\[(\d+)\]", part)
                if match:
                    clean_part, index = match.groups()
                    index = int(index)
                    is_array = True
            
            # Navigate or Create
            if clean_part not in current:
                if is_array:
                    current[clean_part] = []
                else:
                    current[clean_part] = {}
            
            # If we expect an array
            if is_array:
                # Ensure array is big enough
                target_list = current[clean_part]
                while len(target_list) <= index:
                    target_list.append({})
                current = target_list[index]
            else:
                current = current[clean_part]
        
        # Set final leaf value
        last_part = parts[-1]
        current[last_part] = value

    def _resolve_xpath(self, generic_xpath: str, canonical_concrete_path: str) -> str:
        """
        Convert generic mapping XPath to concrete XPath with indices.
        
        Input Mapping: parties[].individual... -> .../PARTY/...
        Input Concrete: parties[0].individual...
        Output Concrete: .../PARTY[0]/...
        """
        # Logic: If canonical path has specific index (parties[0]), 
        # apply that index to the corresponding Repeated Container in MISMO (PARTY).
        
        # This mapping is implicit in our logic:
        # parties[] -> PARTY
        # loans[] -> LOAN
        # assets[] -> ASSET
        # employment[] -> EMPLOYMENT
        # collateral[] -> COLLATERAL
        # addresses[] -> ADDRESS
        
        concrete_xpath = generic_xpath
        
        # Map known containers
        array_map = {
            r"parties\[(\d+)\]": "PARTY",
            r"loans\[(\d+)\]": "LOAN",
            r"assets\[(\d+)\]": "ASSET",
            r"employment\[(\d+)\]": "EMPLOYMENT / EMPLOYER", # EMPLOYMENT usually
            r"income\[(\d+)\]": "INCOME",
            r"collateral\[(\d+)\]": "COLLATERAL",
            r"addresses\[(\d+)\]": "ADDRESS"
        }
        
        for pattern, xml_tag in array_map.items():
            match = re.search(pattern, canonical_concrete_path)
            if match:
                index = match.group(1)
                # Replace generic TAG with TAG[index]
                # Note: This simplistic replacement works for this schema level.
                # If XML tag appears multiple times, we might need smarter replacement, 
                # but valid MISMO structure usually has distinct hierarchy.
                
                # Careful: EMPLOYMENT mapping points to .../EMPLOYMENT/EMPLOYER
                # We need to attach index to the Repeating Container.
                
                if xml_tag == "EMPLOYMENT / EMPLOYER":
                    concrete_xpath = concrete_xpath.replace("/EMPLOYMENT/", f"/EMPLOYMENT[{index}]/")
                elif f"/{xml_tag}/" in concrete_xpath:
                     concrete_xpath = concrete_xpath.replace(f"/{xml_tag}/", f"/{xml_tag}[{index}]/")
                elif concrete_xpath.endswith(f"/{xml_tag}"):
                     concrete_xpath = concrete_xpath + f"[{index}]"
        
        # Safety: Resolve un-indexed parent containers that should be arrays (e.g. PARTY parent of INCOME)
        # If income[] maps to .../PARTY/INCOME..., PARTY is unindexed. Default to PARTY[0].
        known_parents = ["PARTY", "LOAN", "ASSET", "DEAL"]
        for p in known_parents:
            if f"/{p}/" in concrete_xpath:
                concrete_xpath = concrete_xpath.replace(f"/{p}/", f"/{p}[0]/")
                     
        return concrete_xpath

    def _flatten_canonical(self, data: Dict, parent_key: str = '', sep: str = '.') -> List[str]:
        """
        Flatten dictionary to list of dot-notation keys (with array indices).
        Example: ['parties[0].individual.firstName', ...]
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_canonical(v, new_key, sep=sep))
            elif isinstance(v, list):
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                         items.extend(self._flatten_canonical(item, f"{new_key}[{i}]", sep=sep))
                    else:
                        # Simple list of values? Not in our schema, but handle just in case
                        pass
            else:
                items.append(new_key)
        return items

    def map_to_intermediate_json(self, canonical_data: Dict) -> Dict:
        """
        Convert Canonical JSON -> Intermediate MISMO Dictionary
        """
        intermediate = {}
        
        # 1. Start with a list of all concrete paths in the actual data
        flat_keys = self._flatten_canonical(canonical_data)
        
        # 2. For each concrete path, find a matching rule
        for concrete_path in flat_keys:
            # We need to match concrete path 'parties[0].individual.firstName' 
            # to generic rule 'parties[].individual.firstName'
            
            # Remove indices for matching
            generic_path = re.sub(r"\[\d+\]", "[]", concrete_path)
            
            # Find rule
            rule = next((r for r in self.mapping_rules if r["canonicalPath"] == generic_path), None)
            
            if rule:
                value = self._get_value_at_path(canonical_data, concrete_path)
                if value is not None:
                    # Resolve concrete XPath
                    xpath = self._resolve_xpath(rule["mismoXPath"], concrete_path)
                    
                    # Set in intermediate dict
                    self._set_value_at_xpath(intermediate, xpath, value)
        
        return intermediate

    def _dict_to_xml_recurse(self, parent: ET.Element, data: Dict):
        for key, value in data.items():
            if isinstance(value, list):
                # Handle List of Objects (Repeating Elements)
                for item in value:
                    elem = ET.SubElement(parent, key)
                    if isinstance(item, dict):
                         self._dict_to_xml_recurse(elem, item)
                    else:
                        elem.text = str(item)
            elif isinstance(value, dict):
                # Handle Nested Object
                elem = ET.SubElement(parent, key)
                self._dict_to_xml_recurse(elem, value)
            else:
                # Handle Value
                elem = ET.SubElement(parent, key)
                elem.text = str(value)

    def generate_xml(self, intermediate_data: Dict) -> str:
        """
        Convert Intermediate Dict -> MISMO XML String
        """
        # Root is assumed to be in the data key, typically MESSAGE
        if not intermediate_data:
            return ""
            
        root_key = list(intermediate_data.keys())[0]
        root_val = intermediate_data[root_key]
        
        root = ET.Element(root_key)
        self._dict_to_xml_recurse(root, root_val)
        
        # Pretty print using minidom for now as ElementTree doesn't support indent natively in older python
        # Or simple indent function
        ET.indent(root, space="  ", level=0)
        return ET.tostring(root, encoding="unicode", method="xml")

# MCP Entry Points
def generate_mismo_xml(canonical_data: Dict) -> Dict:
    mapper = MismoMapper()
    
    # 1. Intermediate
    intermediate = mapper.map_to_intermediate_json(canonical_data)
    
    # 2. XML
    xml_output = mapper.generate_xml(intermediate)
    
    return {
        "intermediate_json": intermediate,
        "mismo_xml": xml_output
    }
