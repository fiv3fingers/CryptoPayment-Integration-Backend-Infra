from typing import Optional, List, Tuple
from sqlalchemy import select
from models.database_models import Organization, OrganizationMember, User
from models.schemas.organization import (
    OrganizationBase, 
    OrganizationCreate,
    OrganizationCreateResponse,
    OrganizationUpdate
)
from fastapi import HTTPException
import logging
from utils.common import generate_api_credentials, hash_secret
from services.base import BaseService

logger = logging.getLogger(__name__)

class OrganizationService(BaseService[Organization]):
    async def create(self, user_id: Cuid, data: OrganizationCreate) -> tuple[Organization, str]:
        """Create a new organization with API credentials."""
        # Generate API credentials
        api_key, api_secret = generate_api_credentials()
        
        # Create org with hashed secret
        org = Organization(
            name=data.name,
            owner_id=user_id,
            api_key=api_key,
            api_secret=hash_secret(api_secret),
            settlement_currencies=data.settlement_currencies
        )
        try:
            self.db.add(org)
            self.db.commit()
            self.db.refresh(org)
            
            # Add owner as member
            member = OrganizationMember(
                organization_id=org.id,
                user_id=user_id
            )
            self.db.add(member)
            self.db.commit()
            self.db.refresh(member)

            # Return both org and unhashed secret
            return org, api_secret

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating organization: {str(e)}")
            raise HTTPException(status_code=400, detail="Error creating organization")



    async def update(self, organization_id: Cuid, data: OrganizationUpdate) -> Organization:
        """Update an existing organization."""
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        org.settlement_currencies = data.settlement_currencies
        org.name = data.name

        try:
            self.db.commit()
            return org
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating organization: {str(e)}")
            raise HTTPException(status_code=400, detail="Error updating organization")

    async def rotate_api_key(self, organization_id: Cuid) -> tuple[str, str]:
        """Generate new API credentials for organization."""
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        api_key, api_secret = generate_api_credentials()
        
        org.api_key = api_key
        org.api_secret = hash_secret(api_secret)
        
        try:
            self.db.commit()
            return api_key, api_secret
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error rotating API key: {str(e)}")
            raise HTTPException(status_code=400, detail="Error rotating API key")


    async def verify_owner(self, organization_id: Cuid, user_id: Cuid) -> bool:
        """Verify if the user is the owner of the organization."""
        org =  self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org.owner_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail="Only the organization owner can perform this action"
            )
        return True

    async def verify_member(self, organization_id: Cuid, user_id: Cuid) -> bool:
        """Verify if the user is a member of the organization."""
        org =  self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        ).first()
        
        if not member:
            raise HTTPException(
                status_code=403, 
                detail="Only organization members can perform this action"
            )
        return True



    async def add_members(
        self, 
        organization_id: Cuid, 
        user_id: Cuid, 
        member_ids: List[Cuid]
    ) -> Tuple[List[Cuid], List[Cuid]]:
        """Add members to the organization. Only members can add members.
        
        Returns:
            tuple[List[Cuid], List[Cuid]]: Tuple of (successful_ids, failed_ids)
        """
        # Verify member
        await self.verify_member(organization_id, user_id)
        
        successful_ids = []
        failed_ids = []
        
        # Get existing members to avoid duplicates
        existing_members = set(
            member.user_id for member in 
            self.db.query(OrganizationMember)
            .filter(OrganizationMember.organization_id == organization_id)
            .all()
        )
        
        for member_id in member_ids:
            try:
                # Skip if already a member
                if member_id in existing_members:
                    failed_ids.append(member_id)
                    continue
                    
                # Verify user exists
                user = self.db.query(User).get(member_id)
                if not user:
                    failed_ids.append(member_id)
                    continue
                
                # Create new member
                member = OrganizationMember(
                    organization_id=organization_id,
                    user_id=member_id
                )
                self.db.add(member)
                successful_ids.append(member_id)
                
            except Exception as e:
                logger.error(f"Error adding member {member_id}: {str(e)}")
                failed_ids.append(member_id)
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in member addition: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Error performing member addition"
            )
            
        return successful_ids, failed_ids

    async def remove_members(
        self,
        organization_id: Cuid,
        user_id: Cuid,
        member_ids: List[Cuid]
    ) -> Tuple[List[Cuid], List[Cuid]]:
        """Remove members from the organization. Only members can remove members.
        
        Returns:
            tuple[List[Cuid], List[Cuid]]: Tuple of (successful_ids, failed_ids)
        """
        # Verify member
        await self.verify_member(organization_id, user_id)
        
        # Cannot remove the owner
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")

        if org.owner_id in member_ids:
            raise HTTPException(
                status_code=400,
                detail="Cannot remove the organization owner"
            )
        
        successful_ids = []
        failed_ids = []
        
        members_to_remove = (
            self.db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id.in_(member_ids)
            )
            .all()
        )
        
        # Track which IDs were found
        found_ids = set(member.user_id for member in members_to_remove)
        
        # Any IDs not found are considered failed
        failed_ids = [mid for mid in member_ids if mid not in found_ids]
        
        try:
            for member in members_to_remove:
                self.db.delete(member)
                successful_ids.append(member.user_id)
            
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error in member removal: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail="Error performing member removal"
            )
        
        return successful_ids, failed_ids

    async def get_members(self, organization_id: Cuid) -> List[OrganizationMember]:
        """Get all members of an organization."""
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        return self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id
        ).all()

    # FIXME: duplicate of is_member
    async def is_member(self, organization_id: Cuid, user_id: Cuid) -> bool:
        """Check if a user is a member of the organization."""
        org = self.db.query(Organization).get(organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
            
        # Check if user is owner or member
        if org.owner_id == user_id:
            return True
            
        member = self.db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id
        ).first()
        
        return member is not None

    async def get_by_id(self, organization_id: Cuid) -> Optional[Organization]:
        return self.db.query(Organization).get(organization_id)

