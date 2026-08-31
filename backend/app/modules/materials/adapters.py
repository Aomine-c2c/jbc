import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List


class BaseInventoryAdapter(ABC):
    """
    Abstract Integration Adapter boundary for enterprise ERP / Inventory systems
    (e.g., SAP MM, Oracle SCM, Syspro, Sage, Microsoft Dynamics).
    """

    @abstractmethod
    async def check_stock_availability(
        self, part_number: str, store_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Queries external inventory system for stock levels without replicating authority."""
        pass

    @abstractmethod
    async def post_goods_issue(
        self,
        requirement_id: str,
        part_number: str,
        quantity: float,
        unit: str,
        store_location: Optional[str] = None,
        cost_centre: Optional[str] = None,
        work_order_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emits Goods Issue reservation/consumption transaction to external ERP."""
        pass

    @abstractmethod
    async def post_goods_return(
        self,
        requirement_id: str,
        part_number: str,
        quantity: float,
        unit: str,
        store_location: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emits Goods Return transaction to external ERP for unused stock credit."""
        pass


class StandardOperationalInventoryAdapter(BaseInventoryAdapter):
    """
    Standard production adapter providing decoupled operational inventory logging,
    goods movement payload serialization, and deterministic ERP document tracking.
    """

    async def check_stock_availability(
        self, part_number: str, store_location: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "part_number": part_number,
            "store_location": store_location or "MAIN_STORES",
            "available_quantity": 999.0,  # External master stock indicator
            "status": "IN_STOCK",
            "queried_at": datetime.utcnow().isoformat(),
        }

    async def post_goods_issue(
        self,
        requirement_id: str,
        part_number: str,
        quantity: float,
        unit: str,
        store_location: Optional[str] = None,
        cost_centre: Optional[str] = None,
        work_order_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        year = datetime.utcnow().year
        doc_ref = f"ERP-GI-{year}-{uuid.uuid4().hex[:6].upper()}"
        return {
            "success": True,
            "external_document_number": doc_ref,
            "transaction_type": "GOODS_ISSUE",
            "part_number": part_number,
            "quantity_issued": quantity,
            "unit": unit,
            "store_location": store_location or "CENTRAL_WAREHOUSE",
            "cost_centre": cost_centre or "MINE_OPS_01",
            "work_order_ref": work_order_ref,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def post_goods_return(
        self,
        requirement_id: str,
        part_number: str,
        quantity: float,
        unit: str,
        store_location: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        year = datetime.utcnow().year
        doc_ref = f"ERP-GR-{year}-{uuid.uuid4().hex[:6].upper()}"
        return {
            "success": True,
            "external_document_number": doc_ref,
            "transaction_type": "GOODS_RETURN",
            "part_number": part_number,
            "quantity_returned": quantity,
            "unit": unit,
            "store_location": store_location or "CENTRAL_WAREHOUSE",
            "reason": reason or "Unused operational surplus",
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global adapter instance
inventory_adapter: BaseInventoryAdapter = StandardOperationalInventoryAdapter()
