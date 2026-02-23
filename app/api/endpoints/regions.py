"""
Regions and SubZones API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.api.deps import get_current_admin
from app.core.rate_limiter import limiter
from app.schemas.schemas import (
    RegionCreate, RegionUpdate, RegionResponse,
    RegionWithZonesResponse, SubZoneCreate, SubZoneResponse
)
from app.services.crud import (
    create_region, get_region_by_id, get_all_regions,
    update_region, delete_region, create_sub_zone, delete_sub_zone
)


router = APIRouter()


# ============== Public Endpoints ==============

@router.get("", response_model=List[RegionWithZonesResponse])
@limiter.limit("120/minute")
async def list_regions(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all regions with their sub-zones.
    
    Returns:
        List[RegionWithZonesResponse]: List of regions with sub-zones
    """
    regions = await get_all_regions(db)
    return regions


@router.get("/{region_id}", response_model=RegionWithZonesResponse)
@limiter.limit("120/minute")
async def get_region(
    request: Request,
    region_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single region by ID with its sub-zones.
    
    Args:
        region_id: Region unique identifier
        
    Returns:
        RegionWithZonesResponse: Region details with sub-zones
        
    Raises:
        HTTPException: If region not found
    """
    region = await get_region_by_id(db, region_id)
    
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    return region


# ============== Protected Admin Endpoints ==============

@router.post("", response_model=RegionResponse, status_code=status.HTTP_201_CREATED)
async def create_new_region(
    region_data: RegionCreate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new region (Admin only).
    
    Args:
        region_data: Region data to create
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        RegionResponse: Created region details
    """
    region = await create_region(db, region_data)
    return region


@router.put("/{region_id}", response_model=RegionResponse)
async def update_existing_region(
    region_id: str,
    region_data: RegionUpdate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update an existing region (Admin only).
    
    Args:
        region_id: Region unique identifier
        region_data: Region data to update
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        RegionResponse: Updated region details
        
    Raises:
        HTTPException: If region not found
    """
    region = await update_region(db, region_id, region_data)
    
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    return region


@router.delete("/{region_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_region(
    region_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a region and all its sub-zones (Admin only).
    
    Args:
        region_id: Region unique identifier
        current_admin: Authenticated admin
        db: Database session
        
    Raises:
        HTTPException: If region not found
    """
    success = await delete_region(db, region_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    return None


# ============== SubZone Endpoints ==============

@router.post("/{region_id}/zones", response_model=SubZoneResponse, status_code=status.HTTP_201_CREATED)
async def add_zone_to_region(
    region_id: str,
    zone_data: SubZoneCreate,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a sub-zone to a region (Admin only).
    
    Args:
        region_id: Region unique identifier
        zone_data: Sub-zone data to create
        current_admin: Authenticated admin
        db: Database session
        
    Returns:
        SubZoneResponse: Created sub-zone details
        
    Raises:
        HTTPException: If region not found
    """
    # Verify region exists
    region = await get_region_by_id(db, region_id)
    
    if not region:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Region not found"
        )
    
    zone = await create_sub_zone(db, region_id, zone_data)
    return zone


@router.delete("/{region_id}/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_zone_from_region(
    region_id: str,
    zone_id: str,
    current_admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a sub-zone from a region (Admin only).
    
    Args:
        region_id: Region unique identifier
        zone_id: Sub-zone unique identifier
        current_admin: Authenticated admin
        db: Database session
        
    Raises:
        HTTPException: If zone not found
    """
    success = await delete_sub_zone(db, zone_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sub-zone not found"
        )
    
    return None
