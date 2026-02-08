"""
Path Resolver - Array-Aware Path Resolution

Handles complex nested and array paths in canonical schema.
Supports dynamic array creation and index-based insertion.

CRITICAL RULES:
- Dynamically create array nodes as needed
- Never overwrite sibling entries
- Preserve ordering
- Support both index-based and append operations
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from src.utils.logging import logger


class PathSegment:
    """Represents a segment of a dot-notation path."""
    
    def __init__(self, key: str, index: Optional[int] = None, is_array: bool = False):
        self.key = key
        self.index = index
        self.is_array = is_array
    
    def __repr__(self):
        if self.is_array:
            idx_str = str(self.index) if self.index is not None else ""
            return f"{self.key}[{idx_str}]"
        return self.key


class PathResolver:
    """
    Array-aware path resolution utility.
    
    Handles complex paths like:
    - deal.parties[0].individual.first_name
    - deal.parties[].employment[].monthly_income.base
    - deal.assets[1].asset_type.value
    """
    
    def __init__(self):
        """Initialize path resolver."""
        pass
    
    def parse_path(self, path: str) -> List[PathSegment]:
        """
        Parse a dot-notation path into segments.
        
        Supports:
        - Simple keys: "deal.identifiers.loan_id"
        - Array indices: "deal.parties[0].individual.first_name"
        - Array placeholders: "deal.parties[].employment[]"
        
        Args:
            path: Dot-notation path string
        
        Returns:
            List of PathSegment objects
        """
        segments = []
        
        # Split by dots, but preserve array notation
        parts = path.split('.')
        
        for part in parts:
            # Check for array notation: key[index] or key[]
            array_match = re.match(r'^(\w+)\[(\d*)\]$', part)
            
            if array_match:
                key = array_match.group(1)
                index_str = array_match.group(2)
                index = int(index_str) if index_str else None
                segments.append(PathSegment(key, index, is_array=True))
            else:
                segments.append(PathSegment(part, is_array=False))
        
        return segments
    
    def set_value_at_path(
        self,
        root: Dict,
        path: str,
        value: Any,
        index_map: Optional[Dict[str, int]] = None,
        create_missing: bool = True
    ) -> None:
        """
        Set a value at a path, creating intermediate nodes as needed.
        
        Args:
            root: The root dictionary to modify
            path: Dot-notation path
            value: The value to set
            index_map: Optional mapping of array keys to specific indices
            create_missing: Whether to create missing intermediate nodes
        
        Raises:
            KeyError: If path doesn't exist and create_missing is False
            ValueError: If trying to index into non-array
        """
        segments = self.parse_path(path)
        current = root
        
        # Navigate to the parent of the final segment
        for i, segment in enumerate(segments[:-1]):
            current = self._navigate_or_create(
                current,
                segment,
                index_map,
                create_missing,
                is_final=False
            )
        
        # Set the final value
        final_segment = segments[-1]
        
        if final_segment.is_array:
            # Setting a value in an array
            if final_segment.key not in current:
                if create_missing:
                    current[final_segment.key] = []
                else:
                    raise KeyError(f"Array '{final_segment.key}' does not exist")
            
            arr = current[final_segment.key]
            
            if not isinstance(arr, list):
                raise ValueError(f"'{final_segment.key}' is not an array")
            
            # Determine index
            if final_segment.index is not None:
                index = final_segment.index
            elif index_map and final_segment.key in index_map:
                index = index_map[final_segment.key]
            else:
                # Append to array
                index = len(arr)
            
            # Ensure array is large enough
            while len(arr) <= index:
                arr.append({})
            
            arr[index] = value
            
        else:
            # Setting a simple key-value
            current[final_segment.key] = value
        
        logger.debug(f"✅ Set value at path '{path}': {value}")
    
    def get_value_at_path(
        self,
        root: Dict,
        path: str,
        default: Any = None
    ) -> Any:
        """
        Get a value at a path.
        
        Args:
            root: The root dictionary
            path: Dot-notation path
            default: Default value if path doesn't exist
        
        Returns:
            The value at the path, or default if not found
        """
        try:
            segments = self.parse_path(path)
            current = root
            
            for segment in segments:
                if segment.is_array:
                    # Navigate into array
                    if segment.key not in current:
                        return default
                    
                    arr = current[segment.key]
                    
                    if not isinstance(arr, list):
                        return default
                    
                    if segment.index is None:
                        # No index specified, return the whole array
                        current = arr
                    else:
                        # Get specific index
                        if segment.index >= len(arr):
                            return default
                        current = arr[segment.index]
                else:
                    # Navigate into dict
                    if segment.key not in current:
                        return default
                    current = current[segment.key]
            
            return current
            
        except Exception as e:
            logger.debug(f"Failed to get value at path '{path}': {e}")
            return default
    
    def _navigate_or_create(
        self,
        current: Any,
        segment: PathSegment,
        index_map: Optional[Dict[str, int]],
        create_missing: bool,
        is_final: bool
    ) -> Any:
        """
        Navigate to a segment, creating it if necessary.
        
        Args:
            current: Current node
            segment: Path segment to navigate to
            index_map: Index mapping for arrays
            create_missing: Whether to create missing nodes
            is_final: Whether this is the final segment
        
        Returns:
            The node at the segment
        
        Raises:
            KeyError: If node doesn't exist and create_missing is False
        """
        if segment.is_array:
            # Handle array navigation
            if segment.key not in current:
                if create_missing:
                    current[segment.key] = []
                else:
                    raise KeyError(f"Array '{segment.key}' does not exist")
            
            arr = current[segment.key]
            
            if not isinstance(arr, list):
                raise ValueError(f"'{segment.key}' is not an array")
            
            # Determine index
            if segment.index is not None:
                index = segment.index
            elif index_map and segment.key in index_map:
                index = index_map[segment.key]
            else:
                # Default to index 0 for navigation
                index = 0
            
            # Ensure array has element at index
            while len(arr) <= index:
                arr.append({})
            
            return arr[index]
            
        else:
            # Handle dict navigation
            if segment.key not in current:
                if create_missing:
                    current[segment.key] = {}
                else:
                    raise KeyError(f"Key '{segment.key}' does not exist")
            
            return current[segment.key]
    
    def path_exists(self, root: Dict, path: str) -> bool:
        """
        Check if a path exists in the data.
        
        Args:
            root: The root dictionary
            path: Dot-notation path
        
        Returns:
            True if path exists, False otherwise
        """
        try:
            value = self.get_value_at_path(root, path, default=None)
            return value is not None
        except Exception:
            return False
    
    def append_to_array(
        self,
        root: Dict,
        array_path: str,
        value: Any,
        create_missing: bool = True
    ) -> int:
        """
        Append a value to an array at the given path.
        
        Args:
            root: The root dictionary
            array_path: Path to the array (without index)
            value: Value to append
            create_missing: Whether to create the array if it doesn't exist
        
        Returns:
            The index where the value was inserted
        
        Raises:
            ValueError: If path doesn't point to an array
        """
        # Get or create the array
        arr = self.get_value_at_path(root, array_path, default=None)
        
        if arr is None:
            if create_missing:
                # Create the array
                self.set_value_at_path(root, array_path, [])
                arr = self.get_value_at_path(root, array_path)
            else:
                raise ValueError(f"Array at '{array_path}' does not exist")
        
        if not isinstance(arr, list):
            raise ValueError(f"Path '{array_path}' does not point to an array")
        
        # Append the value
        arr.append(value)
        index = len(arr) - 1
        
        logger.debug(f"✅ Appended to array '{array_path}' at index {index}")
        
        return index


# Convenience function for creating resolver instance
def get_path_resolver() -> PathResolver:
    """Get a PathResolver instance."""
    return PathResolver()
