from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Tuple
from uuid import UUID
from sqlalchemy.orm import Session

from database.dependencies import get_db, get_current_user, get_current_organization
from services.organization import OrganizationService
from models.schemas.organization import (
    OrganizationBase,
    OrganizationCreate,
    OrganizationCreateResponse,
    OrganizationUpdate,
    OrganizationFullResponse,
    OrganizationCredentialsResponse,
    MemberOperation,
    MemberOperationResponse,
    OrganizationMemberResponse
)


from models.database_models import User, Organization

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post(
    "",
    response_model=OrganizationCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new organization"
)
async def create_organization(
    data: OrganizationCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    org_service = OrganizationService(db)
    org, secret = await org_service.create(user.id, data)
    return org

@router.post('/update', response_model=OrganizationFullResponse)
async def update_organization(
    data: OrganizationUpdate,
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Update an existing organization."""
    org_service = OrganizationService(db)
    return await org_service.update(organization.id, data)

@router.post(
    "/rotate-key",
    response_model=OrganizationCredentialsResponse,
    summary="Rotate organization API credentials"
)
async def rotate_organization_api_key(
    user: User = Depends(get_current_user),
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Generate new API credentials for the organization."""
    org_service = OrganizationService(db)
    await org_service.verify_owner(organization.id, user.id)
    api_key, api_secret = await org_service.rotate_api_key(organization.id)
    return OrganizationCredentialsResponse(api_key=api_key, api_secret=api_secret)

@router.post(
    "/{organization_id}/members",
    response_model=MemberOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Add members to an organization"
)
async def add_organization_members(
    organization_id: UUID,
    member_data: MemberOperation,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add members to an organization.
    Only the organization owner can add members.
    Returns lists of successful and failed member additions.
    """
    org_service = OrganizationService(db)
    successful_ids, failed_ids = await org_service.add_members(
        organization_id=organization_id,
        user_id=user.id,
        member_ids=member_data.member_ids
    )
    
    return MemberOperationResponse(
        successful_ids=successful_ids,
        failed_ids=failed_ids,
        message=f"Successfully added {len(successful_ids)} members. {len(failed_ids)} failed."
    )

@router.delete(
    "/{organization_id}/members",
    response_model=MemberOperationResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove members from an organization"
)
async def remove_organization_members(
    organization_id: UUID,
    member_data: MemberOperation,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove members from an organization.
    Only the organization owner can remove members.
    Cannot remove the organization owner.
    Returns lists of successful and failed member removals.
    """
    org_service = OrganizationService(db)
    successful_ids, failed_ids = await org_service.remove_members(
        organization_id=organization_id,
        user_id=user.id,
        member_ids=member_data.member_ids
    )
    
    return MemberOperationResponse(
        successful_ids=successful_ids,
        failed_ids=failed_ids,
        message=f"Successfully removed {len(successful_ids)} members. {len(failed_ids)} failed."
    )

@router.get(
    "/{organization_id}/members",
    response_model=List[OrganizationMemberResponse],
    summary="Get all members of an organization"
)
async def get_organization_members(
    organization_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all members of an organization."""
    org_service = OrganizationService(db)
    return await org_service.get_members(organization_id)


@router.get(
    "",
    response_model=OrganizationBase,
    summary="Get information about the current organization"
)
async def get_organization(
    organization: Organization = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    """Get information about the current organization."""
    org_service = OrganizationService(db)
    return await org_service.get_by_id(organization.id)

