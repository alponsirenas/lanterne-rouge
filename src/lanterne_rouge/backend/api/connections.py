"""API endpoints for data connections (Strava, Oura, Apple Health)."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from lanterne_rouge.backend.api.dependencies import get_current_user
from lanterne_rouge.backend.db.session import get_db
from lanterne_rouge.backend.models.connection import DataConnection
from lanterne_rouge.backend.models.user import User
from lanterne_rouge.backend.schemas.connections import (
    AllConnectionsStatus,
    ConnectionStatus,
    StravaAuthRequest,
    StravaAuthResponse,
    StravaCallbackRequest,
    StravaConnectionResponse,
    OuraConnectRequest,
    OuraConnectionResponse,
    AppleHealthUploadResponse,
    DisconnectRequest,
    DisconnectResponse,
    RefreshRequest,
    RefreshResponse,
)
from lanterne_rouge.backend.services.encryption import get_encryption_service
from lanterne_rouge.backend.services.data_connections import (
    get_strava_service,
    get_oura_service,
    get_apple_health_service,
)

router = APIRouter(prefix="/connections", tags=["connections"])
logger = logging.getLogger(__name__)

# Never log secrets
logging.getLogger('lanterne_rouge.backend.services').setLevel(logging.WARNING)


@router.get("/status", response_model=AllConnectionsStatus)
async def get_connections_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get status of all data connections for the current user.

    Returns connection status, last refresh time, and any error messages.
    """
    connections = {}

    for conn_type in ["strava", "oura", "apple_health"]:
        conn = db.query(DataConnection).filter(
            DataConnection.user_id == current_user.id,
            DataConnection.connection_type == conn_type
        ).first()

        if conn:
            connections[conn_type] = ConnectionStatus(
                connection_type=conn.connection_type,
                status=conn.status,
                last_refresh_at=conn.last_refresh_at,
                last_refresh_status=conn.last_refresh_status,
                error_message=conn.error_message
            )

    return AllConnectionsStatus(
        strava=connections.get("strava"),
        oura=connections.get("oura"),
        apple_health=connections.get("apple_health")
    )


@router.post("/strava/authorize", response_model=StravaAuthResponse)
async def authorize_strava(
    request: StravaAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Initiate Strava OAuth2 flow.

    Returns the authorization URL to redirect the user to.
    """
    strava_service = get_strava_service()

    try:
        auth_url = strava_service.get_authorization_url(
            redirect_uri=request.redirect_uri,
            user_id=current_user.id
        )

        return StravaAuthResponse(authorization_url=auth_url)

    except Exception as e:
        logger.error(f"Failed to initiate Strava OAuth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Strava authorization"
        )


@router.post("/strava/callback", response_model=StravaConnectionResponse)
async def strava_callback(
    request: StravaCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Handle Strava OAuth2 callback.

    Exchange authorization code for access and refresh tokens.
    """
    strava_service = get_strava_service()
    encryption_service = get_encryption_service()

    try:
        # Exchange code for tokens
        tokens = strava_service.exchange_code_for_tokens(request.code)

        # Encrypt the tokens
        encrypted = encryption_service.encrypt_credentials(tokens)

        # Store or update connection
        conn = db.query(DataConnection).filter(
            DataConnection.user_id == current_user.id,
            DataConnection.connection_type == "strava"
        ).first()

        if conn:
            conn.encrypted_credentials = encrypted
            conn.status = "connected"
            conn.error_message = None
            conn.updated_at = datetime.now(timezone.utc)
        else:
            conn = DataConnection(
                user_id=current_user.id,
                connection_type="strava",
                status="connected",
                encrypted_credentials=encrypted
            )
            db.add(conn)

        db.commit()
        db.refresh(conn)

        logger.info(f"Strava connected successfully for user {current_user.id}")

        return StravaConnectionResponse(
            message="Strava connected successfully",
            status=ConnectionStatus(
                connection_type=conn.connection_type,
                status=conn.status,
                last_refresh_at=conn.last_refresh_at,
                last_refresh_status=conn.last_refresh_status,
                error_message=conn.error_message
            )
        )

    except Exception as e:
        logger.error(f"Strava callback failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to connect Strava account"
        )


@router.post("/oura/connect", response_model=OuraConnectionResponse)
async def connect_oura(
    request: OuraConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Connect Oura account using Personal Access Token.

    Validates the token and stores it securely.
    """
    oura_service = get_oura_service()
    encryption_service = get_encryption_service()

    try:
        # Validate the token
        is_valid = oura_service.validate_token(request.personal_access_token)

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Oura Personal Access Token"
            )

        # Encrypt the token
        credentials = {"personal_access_token": request.personal_access_token}
        encrypted = encryption_service.encrypt_credentials(credentials)

        # Store or update connection
        conn = db.query(DataConnection).filter(
            DataConnection.user_id == current_user.id,
            DataConnection.connection_type == "oura"
        ).first()

        if conn:
            conn.encrypted_credentials = encrypted
            conn.status = "connected"
            conn.error_message = None
            conn.updated_at = datetime.now(timezone.utc)
        else:
            conn = DataConnection(
                user_id=current_user.id,
                connection_type="oura",
                status="connected",
                encrypted_credentials=encrypted
            )
            db.add(conn)

        db.commit()
        db.refresh(conn)

        logger.info(f"Oura connected successfully for user {current_user.id}")

        return OuraConnectionResponse(
            message="Oura connected successfully",
            status=ConnectionStatus(
                connection_type=conn.connection_type,
                status=conn.status,
                last_refresh_at=conn.last_refresh_at,
                last_refresh_status=conn.last_refresh_status,
                error_message=conn.error_message
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Oura connection failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect Oura account"
        )


@router.post("/apple-health/upload", response_model=AppleHealthUploadResponse)
async def upload_apple_health(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload Apple Health export file (ZIP or XML).

    Parses the export and stores daily metrics.
    """
    apple_health_service = get_apple_health_service()

    try:
        # Validate file type
        if not (file.filename.endswith('.zip') or file.filename.endswith('.xml')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be a ZIP or XML export from Apple Health"
            )

        # Read file content
        content = await file.read()

        # Parse and process the export
        upload_batch_id, records = apple_health_service.process_export(
            content,
            file.filename,
            current_user.id,
            db
        )

        # Update connection status
        conn = db.query(DataConnection).filter(
            DataConnection.user_id == current_user.id,
            DataConnection.connection_type == "apple_health"
        ).first()

        if conn:
            conn.status = "connected"
            conn.last_refresh_at = datetime.now(timezone.utc)
            conn.last_refresh_status = f"Processed {records} records"
            conn.error_message = None
            conn.updated_at = datetime.now(timezone.utc)
        else:
            conn = DataConnection(
                user_id=current_user.id,
                connection_type="apple_health",
                status="connected",
                last_refresh_at=datetime.now(timezone.utc),
                last_refresh_status=f"Processed {records} records"
            )
            db.add(conn)

        db.commit()

        logger.info(f"Apple Health data uploaded for user {current_user.id}: {records} records")

        return AppleHealthUploadResponse(
            message="Apple Health data uploaded successfully",
            records_processed=records,
            upload_batch_id=upload_batch_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Apple Health upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process Apple Health export"
        )


@router.post("/disconnect", response_model=DisconnectResponse)
async def disconnect_source(
    request: DisconnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Disconnect a data source.

    Removes stored credentials and updates connection status.
    """
    if request.connection_type not in ["strava", "oura", "apple_health"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid connection type"
        )

    conn = db.query(DataConnection).filter(
        DataConnection.user_id == current_user.id,
        DataConnection.connection_type == request.connection_type
    ).first()

    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )

    # Clear credentials and update status
    conn.encrypted_credentials = None
    conn.status = "disconnected"
    conn.error_message = None
    conn.updated_at = datetime.now(timezone.utc)

    db.commit()

    logger.info(f"{request.connection_type} disconnected for user {current_user.id}")

    return DisconnectResponse(
        message=f"{request.connection_type.title()} disconnected successfully"
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_data(
    request: RefreshRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Manually trigger a data refresh from a connected source.

    Fetches latest data and updates the database.
    """
    if request.connection_type not in ["strava", "oura", "apple_health"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid connection type"
        )

    conn = db.query(DataConnection).filter(
        DataConnection.user_id == current_user.id,
        DataConnection.connection_type == request.connection_type
    ).first()

    if not conn or conn.status != "connected":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{request.connection_type.title()} is not connected"
        )

    # Check if manual refresh is supported
    if request.connection_type == "apple_health":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Manual refresh not supported for Apple Health. Please upload a new export."
        )

    try:
        # Call appropriate service to refresh data
        if request.connection_type == "strava":
            service = get_strava_service()
            records = service.refresh_activities(current_user.id, conn, db)
        elif request.connection_type == "oura":
            service = get_oura_service()
            records = service.refresh_readiness_data(current_user.id, conn, db)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid connection type"
            )

        # Update connection status
        conn.last_refresh_at = datetime.now(timezone.utc)
        conn.last_refresh_status = f"Refreshed {records} records"
        conn.error_message = None
        db.commit()

        return RefreshResponse(
            message=f"Successfully refreshed {request.connection_type} data",
            records_updated=records,
            last_refresh_at=conn.last_refresh_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Data refresh failed for {request.connection_type}: {str(e)}")

        # Update connection with error
        conn.error_message = str(e)
        conn.updated_at = datetime.now(timezone.utc)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh {request.connection_type} data"
        )
