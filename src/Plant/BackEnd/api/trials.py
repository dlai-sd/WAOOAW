"""
Trial API Endpoints

FastAPI routes for trial management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.trial import TrialStatus
from schemas.trial import (
    TrialCreate,
    TrialUpdate,
    TrialResponse,
    TrialListResponse,
    TrialDeliverableResponse
)
from services.trial_service import TrialService
from core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/trials", tags=["trials"])


def get_trial_service(db: AsyncSession = Depends(get_db_session)) -> TrialService:
    """Dependency to get trial service instance."""
    return TrialService(db)


from .factorial import get_factorial

# Removed the old get_factorial function definition


@router.post(
    "",
    response_model=TrialResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create Trial",
    description="Create a new 7-day trial for a customer",
)
async def create_trial(
    trial_data: TrialCreate,
    service: TrialService = Depends(get_trial_service),
) -> TrialResponse:
    """Create a new trial.

    Returns the created trial, including computed days_remaining.
    """
    try:
        trial = await service.create_trial(trial_data)
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create trial: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trial",
        )

    try:
        response = TrialResponse.from_orm(trial)
        response.days_remaining = trial.days_remaining
        return response
    except ValidationError as e:
        logger.error(f"Failed to serialize created trial response: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to serialize created trial",
        )


@router.get(
    "",
    response_model=TrialListResponse,
    summary="List Trials",
    description="List trials with optional filters and pagination"
)
async def list_trials(
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    trial_status: Optional[TrialStatus] = Query(
        None,
        alias="status",
        description="Filter by status",
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    service: TrialService = Depends(get_trial_service)
) -> TrialListResponse:
    """
    List trials with filters.
    
    **Query Parameters:**
    - customer_email: Filter by customer email (optional)
    - status: Filter by status (active/converted/cancelled/expired) (optional)
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 1000)
    
    **Returns:**
    - List of trials matching filters
    - Total count (ignoring pagination)
    - Pagination metadata
    
    **TODO:** Add authentication - filter by current user's email only
    """
    try:
        trials, total = await service.list_trials(
            customer_email=customer_email,
            status=trial_status,
            skip=skip,
            limit=limit
        )
        
        # Convert to response models with days_remaining
        trial_responses = []
        for trial in trials:
            response = TrialResponse.from_orm(trial)
            response.days_remaining = trial.days_remaining
            trial_responses.append(response)
        
        return TrialListResponse(
            trials=trial_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list trials: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list trials"
        )


@router.get(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Get Trial",
    description="Get trial details by ID"
)
async def get_trial(
    trial_id: UUID,
    service: TrialService = Depends(get_trial_service)
) -> TrialResponse:
    """
    Get trial by ID.
    
    **Path Parameters:**
    - trial_id: UUID of trial
    
    **Returns:**
    - Trial object with all fields
    
    **Errors:**
    - 404: Trial not found
    
    **TODO:** Add authentication - verify user owns this trial
    """
    trial = await service.get_trial(trial_id)
    
    if not trial:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Trial {trial_id} not found"
        )
    
    response = TrialResponse.from_orm(trial)
    response.days_remaining = trial.days_remaining
    
    return response


@router.patch(
    "/{trial_id}",
    response_model=TrialResponse,
    summary="Update Trial Status",
    description="Update trial status (convert, cancel, expire)"
)
async def update_trial_status(
    trial_id: UUID,
    status_update: TrialUpdate,
    service: TrialService = Depends(get_trial_service)
) -> TrialResponse:
    """
    Update trial status.
    
    **Path Parameters:**
    - trial_id: UUID of trial
    
    **Request Body:**
    - status: New status (converted/cancelled/expired)
    
    **Status Transitions:**
    - active → converted (customer keeps agent, starts subscription)
    - active → cancelled (customer cancels, keeps deliverables)
    - active → expired (trial ended without conversion)
    
    **Returns:**
    - Updated trial object
    
    **Errors:**
    - 404: Trial not found
    - 400: Invalid status transition
    
    **TODO:** Add authentication - verify user owns this trial
    """
    try:
        trial = await service.update_trial_status(trial_id, status_update)
        
        if not trial:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Trial {trial_id} not found"
            )
        
        response = TrialResponse.from_orm(trial)
        response.days_remaining = trial.days_remaining
        
        logger.info(f"Trial {trial_id} status updated to {status_update.status}")
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update trial {trial_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update trial"
        )


@router.delete(
    "/{trial_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Cancel Trial",
    description="Cancel a trial (convenience endpoint)"
)
async def cancel_trial(
    trial_id: UUID,
    service: TrialService = Depends(get_trial_service)
) -> None:
    """
    Cancel a trial.
    
    Convenience endpoint - equivalent to PATCH with status=cancelled.
    
    **Path Parameters:**
    - trial_id: UUID of trial
    
    **Returns:**
    - 204 No Content on success
    
    **Errors:**
    - 404: Trial not found
    - 400: Trial already in final state
    
    **TODO:** Add authentication - verify user owns this trial
    """
    try:
        trial = await service.cancel_trial(trial_id)
        
        if not trial:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Trial {trial_id} not found"
            )
        
        logger.info(f"Trial {trial_id} cancelled via API")
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to cancel trial {trial_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel trial"
        )


@router.get(
    "/{trial_id}/deliverables",
    response_model=list[TrialDeliverableResponse],
    summary="Get Trial Deliverables",
    description="Get all deliverables for a trial"
)
async def get_trial_deliverables(
    trial_id: UUID,
    service: TrialService = Depends(get_trial_service)
) -> list[TrialDeliverableResponse]:
    """
    Get trial deliverables.
    
    **Path Parameters:**
    - trial_id: UUID of trial
    
    **Returns:**
    - List of deliverables (files produced during trial)
    - Customers keep these even if trial cancelled
    
    **TODO:** Add authentication - verify user owns this trial
    **TODO:** Add download URLs (presigned S3/GCS URLs)
    """
    # Verify trial exists
    trial = await service.get_trial(trial_id)
    if not trial:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Trial {trial_id} not found"
        )
    
    try:
        deliverables = await service.get_trial_deliverables(trial_id)
        return [TrialDeliverableResponse.from_orm(d) for d in deliverables]
        
    except Exception as e:
        logger.error(f"Failed to get deliverables for trial {trial_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get deliverables"
        )
