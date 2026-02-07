"""
Asset Mapper
Maps assets table data to MISMO ASSET fields
"""
from . import enums
from typing import Dict


def map_asset_type(db_value: str) -> str:
    """Map asset_type to MISMO AssetType"""
    if not db_value:
        return "OtherAsset"
    return enums.ASSET_TYPE.get(db_value.upper(), db_value)


def map_asset_category(db_value: str) -> str:
    """Map asset_category to MISMO category"""
    if not db_value:
        return "Liquid"
    return enums.ASSET_CATEGORY.get(db_value.upper(), db_value)


def map_gift_type(db_value: str) -> str:
    """Map gift_type to MISMO gift classification"""
    if not db_value:
        return ""
    return enums.GIFT_TYPE.get(db_value.upper(), db_value)


def format_asset_value(value) -> str:
    """Format asset value for MISMO"""
    if value is None:
        return "0"
    try:
        return str(float(value))
    except (ValueError, TypeError):
        return "0"


def extract_asset_details(asset: Dict) -> Dict:
    """Extract all asset details for MISMO"""
    return {
        "asset_type": map_asset_type(asset.get("asset_type")),
        "asset_category": map_asset_category(asset.get("asset_category")),
        "institution_name": asset.get("institution_name") or "",
        "account_number": asset.get("account_number") or "",
        "cash_or_market_value": format_asset_value(asset.get("cash_or_market_value")),
        "is_gift_or_grant": asset.get("is_gift_or_grant", False),
        "gift_type": map_gift_type(asset.get("gift_type")) if asset.get("is_gift_or_grant") else "",
        "gift_source": asset.get("gift_source") or "",
        "verified_value": format_asset_value(asset.get("verified_value")),
        "description": asset.get("description") or ""
    }
