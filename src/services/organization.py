from typing import Optional, List
from src.models.database_models import Organization, SettlementCurrency

from src.services.base import BaseService

from fastapi import HTTPException

import logging

logger = logging.getLogger(__name__)

class OrganizationService(BaseService[Organization]):
    async def get_by_id(self, organization_id: str) -> Optional[Organization]:
        return self.db.query(Organization).get(organization_id)

    async def get_settlement_currencies(self, organization_id: str) -> List[SettlementCurrency]:
        """Get settlement currencies for the organization."""
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        settlement_currencies = [
            SettlementCurrency.from_dict(currency) for currency in org.settlement_currencies
        ]
        
        return settlement_currencies
        



