"""
Enum Validator - Strict Enumeration Enforcement

Validates that field values conform to schema-defined enumerations.
Enforces MISMO 3.4 enum structure: {value, options}

CRITICAL RULES:
- NO auto-correction
- NO closest-match guessing
- NO silent fallbacks
- Raise StructuredMappingError on violation
"""

from typing import Any, List, Optional, Dict
from utils.logging import logger


class StructuredMappingError(Exception):
    """Raised when enum validation fails or mapping violates schema constraints."""
    pass


class EnumValidator:
    """
    Strict enum validation utility.
    
    Validates that values conform to schema-defined enum options.
    Never auto-corrects or guesses - fails fast on violations.
    """
    
    def __init__(self):
        """Initialize enum validator."""
        pass
    
    def validate_enum_value(
        self,
        field_path: str,
        value: Any,
        options: List[str],
        allow_null: bool = True
    ) -> None:
        """
        Validate that a value is in the allowed enum options.
        
        Args:
            field_path: Dot-notation path to the field (for error messages)
            value: The value to validate
            options: List of valid enum options
            allow_null: Whether to allow None/null values
        
        Raises:
            StructuredMappingError: If value is not in options
        """
        # Allow null values if configured
        if value is None and allow_null:
            return
        
        # Convert value to string for comparison
        value_str = str(value) if value is not None else None
        
        # Check if value is in options
        if value_str not in options:
            error_msg = (
                f"Enum validation failed for '{field_path}': "
                f"value '{value}' is not in allowed options {options}"
            )
            logger.error(error_msg)
            raise StructuredMappingError(error_msg)
        
        logger.debug(f"✅ Enum validation passed for '{field_path}': {value}")
    
    def is_enum_field(self, schema_node: Any) -> bool:
        """
        Check if a schema node represents an enum field.
        
        An enum field has the structure:
        {
            "value": <current_value>,
            "options": [<valid_options>]
        }
        
        Args:
            schema_node: The schema node to check
        
        Returns:
            True if node is an enum field, False otherwise
        """
        if not isinstance(schema_node, dict):
            return False
        
        return 'value' in schema_node and 'options' in schema_node
    
    def get_enum_options(self, schema_node: Dict) -> Optional[List[str]]:
        """
        Extract enum options from a schema node.
        
        Args:
            schema_node: The schema node containing enum definition
        
        Returns:
            List of valid enum options, or None if not an enum field
        """
        if not self.is_enum_field(schema_node):
            return None
        
        options = schema_node.get('options', [])
        
        if not isinstance(options, list):
            logger.warning(f"Enum options is not a list: {options}")
            return None
        
        return options
    
    def validate_and_structure_enum(
        self,
        field_path: str,
        value: Any,
        options: List[str],
        allow_null: bool = True
    ) -> Dict[str, Any]:
        """
        Validate an enum value and return it in the proper structure.
        
        Args:
            field_path: Dot-notation path to the field
            value: The value to validate
            options: List of valid enum options
            allow_null: Whether to allow None/null values
        
        Returns:
            Dictionary with {value, options} structure
        
        Raises:
            StructuredMappingError: If value is not in options
        """
        # Validate the value
        self.validate_enum_value(field_path, value, options, allow_null)
        
        # Return structured enum
        return {
            "value": value,
            "options": options
        }
    
    def extract_enum_value(self, enum_field: Dict) -> Any:
        """
        Extract the value from an enum field structure.
        
        Args:
            enum_field: Dictionary with {value, options} structure
        
        Returns:
            The value, or None if not found
        """
        if not isinstance(enum_field, dict):
            return None
        
        return enum_field.get('value')
    
    def validate_enum_structure(self, enum_field: Dict, field_path: str = "") -> bool:
        """
        Validate that an enum field has the correct structure.
        
        Args:
            enum_field: The enum field to validate
            field_path: Path for error messages
        
        Returns:
            True if structure is valid
        
        Raises:
            StructuredMappingError: If structure is invalid
        """
        if not isinstance(enum_field, dict):
            raise StructuredMappingError(
                f"Enum field at '{field_path}' must be a dictionary, got {type(enum_field)}"
            )
        
        if 'value' not in enum_field:
            raise StructuredMappingError(
                f"Enum field at '{field_path}' missing 'value' key"
            )
        
        if 'options' not in enum_field:
            raise StructuredMappingError(
                f"Enum field at '{field_path}' missing 'options' key"
            )
        
        if not isinstance(enum_field['options'], list):
            raise StructuredMappingError(
                f"Enum field at '{field_path}' has invalid 'options' (must be a list)"
            )
        
        return True


# Convenience function for creating validator instance
def get_enum_validator() -> EnumValidator:
    """Get an EnumValidator instance."""
    return EnumValidator()
