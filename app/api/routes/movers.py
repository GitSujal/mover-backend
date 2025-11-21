"""Mover routes for organization and fleet management."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_active_user
from app.core.database import get_db
from app.models.user import User, UserRole
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
)
from app.schemas.truck import TruckCreate, TruckResponse, TruckUpdate
from app.services.movers import MoverService

router = APIRouter(prefix="/movers", tags=["Movers"])


# Organization Endpoints


@router.post(
    "/organizations",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    org_data: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    # In a real app, this might be open or protected by admin
) -> OrganizationResponse:
    """Register a new mover organization."""
    # Check if email already exists (should be handled by service/model constraint)
    try:
        org = await MoverService.create_organization(db, org_data)
        return OrganizationResponse.model_validate(org)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/organizations/me", response_model=OrganizationResponse)
async def get_my_organization(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """Get current user's organization details."""
    org = await MoverService.get_organization(db, current_user.org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return OrganizationResponse.model_validate(org)


@router.patch("/organizations/me", response_model=OrganizationResponse)
async def update_my_organization(
    update_data: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> OrganizationResponse:
    """Update current user's organization."""
    if current_user.role not in [UserRole.ORG_OWNER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only organization owners can update details",
        )

    org = await MoverService.get_organization(db, current_user.org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    org = await MoverService.update_organization(db, org, update_data)
    return OrganizationResponse.model_validate(org)


# Truck Endpoints


@router.get("/trucks", response_model=list[TruckResponse])
async def list_trucks(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[TruckResponse]:
    """List trucks in the organization."""
    trucks = await MoverService.list_trucks(db, current_user.org_id, limit=limit, offset=offset)
    # Manually map location for response
    return [
        TruckResponse(
            **truck.__dict__,
            base_location_lat=db.scalar(truck.base_location.ST_Y()) if truck.base_location else 0.0,
            base_location_lng=db.scalar(truck.base_location.ST_X()) if truck.base_location else 0.0,
        )
        for truck in trucks
    ]


@router.post("/trucks", response_model=TruckResponse, status_code=status.HTTP_201_CREATED)
async def create_truck(
    truck_data: TruckCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TruckResponse:
    """Add a new truck to the fleet."""
    if current_user.role not in [UserRole.ORG_OWNER, UserRole.ORG_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    try:
        truck = await MoverService.create_truck(db, current_user.org_id, truck_data)
        # Refresh to get ID and other DB defaults
        return TruckResponse(
            **truck.__dict__,
            base_location_lat=truck_data.base_location.latitude,
            base_location_lng=truck_data.base_location.longitude,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/trucks/{truck_id}", response_model=TruckResponse)
async def get_truck(
    truck_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TruckResponse:
    """Get truck details."""
    truck = await MoverService.get_truck(db, truck_id)
    if not truck or truck.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    # Need to fetch coordinates from PostGIS geometry
    # This is a bit hacky, ideally we'd use a proper serializer or hybrid property
    # For now, let's assume the service/model handles it or we query it explicitly
    # Re-querying for simplicity in this context
    from sqlalchemy import func

    lat = await db.scalar(select(func.ST_Y(truck.base_location)))
    lng = await db.scalar(select(func.ST_X(truck.base_location)))

    return TruckResponse(
        **truck.__dict__,
        base_location_lat=lat,
        base_location_lng=lng,
    )


@router.patch("/trucks/{truck_id}", response_model=TruckResponse)
async def update_truck(
    truck_id: UUID,
    update_data: TruckUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> TruckResponse:
    """Update truck details."""
    if current_user.role not in [UserRole.ORG_OWNER, UserRole.ORG_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    truck = await MoverService.get_truck(db, truck_id)
    if not truck or truck.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found",
        )

    truck = await MoverService.update_truck(db, truck, update_data)

    from sqlalchemy import func

    lat = await db.scalar(select(func.ST_Y(truck.base_location)))
    lng = await db.scalar(select(func.ST_X(truck.base_location)))

    return TruckResponse(
        **truck.__dict__,
        base_location_lat=lat,
        base_location_lng=lng,
    )


# Driver Endpoints


@router.get("/drivers", response_model=list[DriverResponse])
async def list_drivers(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[DriverResponse]:
    """List drivers in the organization."""
    drivers = await MoverService.list_drivers(db, current_user.org_id, limit=limit, offset=offset)
    return [DriverResponse.model_validate(d) for d in drivers]


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver_data: DriverCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Add a new driver to the fleet."""
    if current_user.role not in [UserRole.ORG_OWNER, UserRole.ORG_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    try:
        driver = await MoverService.create_driver(db, current_user.org_id, driver_data)
        return DriverResponse.model_validate(driver)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/drivers/{driver_id}", response_model=DriverResponse)
async def get_driver(
    driver_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Get driver details."""
    driver = await MoverService.get_driver(db, driver_id)
    if not driver or driver.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )
    return DriverResponse.model_validate(driver)


@router.patch("/drivers/{driver_id}", response_model=DriverResponse)
async def update_driver(
    driver_id: UUID,
    update_data: DriverUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DriverResponse:
    """Update driver details."""
    if current_user.role not in [UserRole.ORG_OWNER, UserRole.ORG_MANAGER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    driver = await MoverService.get_driver(db, driver_id)
    if not driver or driver.org_id != current_user.org_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found",
        )

    driver = await MoverService.update_driver(db, driver, update_data)
    return DriverResponse.model_validate(driver)
