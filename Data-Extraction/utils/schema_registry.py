"""
Schema Registry - Singleton for Canonical Schema Management

Provides centralized access to the MISMO 3.4-aligned canonical schema.
Ensures schema is loaded once and cached for performance.

CRITICAL RULES:
- Schema loaded from resources/canonical_schema/schema.json ONLY
- No hardcoded schema structures
- No fallback schemas
- Validates schema structure on load
"""

import json
import os
from typing import Dict, List, Optional, Any, Set
from utils.logging import logger


class SchemaRegistry:
    """
    Singleton registry for canonical schema management.
    
    Responsibilities:
    - Load schema once from disk
    - Validate schema structure
    - Provide path validation
    - Expose enum options
    - Detect array nodes
    """
    
    _instance = None
    _schema = None
    _schema_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SchemaRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'SchemaRegistry':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """Initialize registry and load schema."""
        if not SchemaRegistry._schema_loaded:
            self._load_schema()
            SchemaRegistry._schema_loaded = True
    
    def _load_schema(self) -> None:
        """Load canonical schema from resources."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            schema_path = os.path.join(
                base_path,
                "resources",
                "canonical_schema",
                "schema.json"
            )
            
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"Canonical schema not found at {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                SchemaRegistry._schema = json.load(f)
            
            # Validate schema structure
            self._validate_schema_structure()
            
            # Extract schema version
            version = SchemaRegistry._schema.get("document_metadata", {}).get("schema_version", "unknown")
            
            logger.info(f"✅ Canonical schema v{version} loaded successfully from {schema_path}")
            
        except FileNotFoundError as e:
            logger.error(f"Schema file not found: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in schema file: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load canonical schema: {e}")
            raise
    
    def _validate_schema_structure(self) -> None:
        """Validate that schema has required structure."""
        if not isinstance(SchemaRegistry._schema, dict):
            raise ValueError("Schema must be a dictionary")
        
        # Check for required top-level keys
        required_keys = ["document_metadata", "deal"]
        for key in required_keys:
            if key not in SchemaRegistry._schema:
                raise ValueError(f"Schema missing required key: {key}")
        
        logger.debug("Schema structure validation passed")
    
    def get_schema(self) -> Dict:
        """Get the complete canonical schema."""
        if SchemaRegistry._schema is None:
            raise RuntimeError("Schema not loaded")
        return SchemaRegistry._schema
    
    def validate_path(self, path: str) -> bool:
        """
        Validate if a path exists in the schema.
        
        Args:
            path: Dot-notation path (e.g., "deal.parties[].individual.first_name")
        
        Returns:
            True if path is valid, False otherwise
        """
        try:
            # Remove array indices for schema validation
            clean_path = path.replace('[]', '[0]')
            
            # Navigate schema to validate path
            parts = self._parse_path(clean_path)
            current = SchemaRegistry._schema
            
            for part in parts:
                if part['type'] == 'key':
                    if part['name'] not in current:
                        return False
                    current = current[part['name']]
                elif part['type'] == 'index':
                    if not isinstance(current, list):
                        return False
                    if len(current) == 0:
                        return False
                    current = current[0]  # Use first element as template
            
            return True
            
        except Exception as e:
            logger.debug(f"Path validation failed for '{path}': {e}")
            return False
    
    def get_enum_options(self, path: str) -> Optional[List[str]]:
        """
        Get enum options for a field if it's an enum type.
        
        Args:
            path: Dot-notation path to the field
        
        Returns:
            List of valid enum options, or None if not an enum field
        """
        try:
            node = self._get_node_at_path(path)
            
            if isinstance(node, dict) and 'options' in node:
                return node['options']
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to get enum options for '{path}': {e}")
            return None
    
    def is_enum_field(self, path: str) -> bool:
        """
        Check if a field is an enum type (has value + options structure).
        
        Args:
            path: Dot-notation path to the field
        
        Returns:
            True if field is an enum, False otherwise
        """
        try:
            node = self._get_node_at_path(path)
            
            if isinstance(node, dict):
                return 'value' in node and 'options' in node
            
            return False
            
        except Exception:
            return False
    
    def is_array_node(self, path: str) -> bool:
        """
        Check if a path points to an array node.
        
        Args:
            path: Dot-notation path
        
        Returns:
            True if node is an array, False otherwise
        """
        try:
            # Remove trailing [] if present
            clean_path = path.rstrip('[]')
            node = self._get_node_at_path(clean_path)
            
            return isinstance(node, list)
            
        except Exception:
            return False
    
    def _get_node_at_path(self, path: str) -> Any:
        """
        Navigate to a node in the schema using dot notation.
        
        Args:
            path: Dot-notation path
        
        Returns:
            The schema node at the path
        
        Raises:
            KeyError: If path doesn't exist
        """
        # Remove array indices for schema navigation
        clean_path = path.replace('[]', '[0]')
        
        parts = self._parse_path(clean_path)
        current = SchemaRegistry._schema
        
        for part in parts:
            if part['type'] == 'key':
                current = current[part['name']]
            elif part['type'] == 'index':
                if isinstance(current, list) and len(current) > 0:
                    current = current[0]  # Use first element as template
                else:
                    raise KeyError(f"Cannot index into non-list or empty list at {path}")
        
        return current
    
    def _parse_path(self, path: str) -> List[Dict[str, Any]]:
        """
        Parse a dot-notation path into segments.
        
        Args:
            path: Dot-notation path (e.g., "deal.parties[0].individual.first_name")
        
        Returns:
            List of path segments with type and name
        """
        segments = []
        parts = path.split('.')
        
        for part in parts:
            if '[' in part and ']' in part:
                # Handle array access: "parties[0]"
                name = part[:part.index('[')]
                index_str = part[part.index('[') + 1:part.index(']')]
                
                segments.append({'type': 'key', 'name': name})
                segments.append({'type': 'index', 'value': int(index_str) if index_str.isdigit() else 0})
            else:
                segments.append({'type': 'key', 'name': part})
        
        return segments
    
    def get_all_enum_paths(self) -> Set[str]:
        """
        Get all paths in the schema that are enum fields.
        
        Returns:
            Set of dot-notation paths to enum fields
        """
        enum_paths = set()
        self._collect_enum_paths(SchemaRegistry._schema, "", enum_paths)
        return enum_paths
    
    def _collect_enum_paths(self, node: Any, current_path: str, enum_paths: Set[str]) -> None:
        """Recursively collect all enum field paths."""
        if isinstance(node, dict):
            # Check if this is an enum field
            if 'value' in node and 'options' in node:
                enum_paths.add(current_path)
            else:
                # Recurse into dict
                for key, value in node.items():
                    new_path = f"{current_path}.{key}" if current_path else key
                    self._collect_enum_paths(value, new_path, enum_paths)
        
        elif isinstance(node, list) and len(node) > 0:
            # Use first element as template
            new_path = f"{current_path}[]" if current_path else "[]"
            self._collect_enum_paths(node[0], new_path, enum_paths)


# Convenience function for getting the singleton instance
def get_schema_registry() -> SchemaRegistry:
    """Get the SchemaRegistry singleton instance."""
    return SchemaRegistry.get_instance()
