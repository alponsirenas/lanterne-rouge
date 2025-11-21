"""Services for data connections (Strava, Oura, Apple Health)."""
import json
import logging
import os
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Optional, Tuple
from xml.etree import ElementTree as ET

import requests
from sqlalchemy.orm import Session

from lanterne_rouge.backend.models.connection import (
    DataConnection, StravaActivity, OuraData, AppleHealthData
)
from lanterne_rouge.backend.services.encryption import get_encryption_service

logger = logging.getLogger(__name__)

# Strava API configuration
STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")
STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

# Oura API configuration
OURA_API_BASE = "https://api.ouraring.com/v2/usercollection"


class StravaService:
    """Service for Strava OAuth2 and data ingestion."""
    
    def get_authorization_url(self, redirect_uri: str, user_id: int) -> str:
        """
        Generate Strava OAuth2 authorization URL.
        
        Args:
            redirect_uri: Where to redirect after authorization
            user_id: User ID for state parameter
            
        Returns:
            Authorization URL string
        """
        params = {
            "client_id": STRAVA_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "read,activity:read_all",
            "state": str(user_id)  # Include user_id in state for verification
        }
        
        from urllib.parse import urlencode
        return f"{STRAVA_AUTHORIZE_URL}?{urlencode(params)}"
    
    def exchange_code_for_tokens(self, code: str) -> dict:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            code: Authorization code from OAuth callback
            
        Returns:
            Dictionary with access_token, refresh_token, expires_at, athlete info
        """
        data = {
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        response = requests.post(STRAVA_TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": token_data["expires_at"],
            "athlete_id": token_data["athlete"]["id"]
        }
    
    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dictionary with new access_token, refresh_token, expires_at
        """
        data = {
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(STRAVA_TOKEN_URL, data=data, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        
        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_at": token_data["expires_at"]
        }
    
    def get_valid_access_token(self, connection: DataConnection, db: Session) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Args:
            connection: DataConnection object with encrypted credentials
            db: Database session
            
        Returns:
            Valid access token
        """
        encryption_service = get_encryption_service()
        credentials = encryption_service.decrypt_credentials(connection.encrypted_credentials)
        
        # Check if token is expired (with 5 minute buffer)
        expires_at = credentials.get("expires_at", 0)
        now = datetime.now(timezone.utc).timestamp()
        
        if expires_at - now < 300:  # Less than 5 minutes until expiry
            logger.info(f"Refreshing expired Strava token for user {connection.user_id}")
            
            # Refresh the token
            new_tokens = self.refresh_access_token(credentials["refresh_token"])
            
            # Update credentials
            credentials.update(new_tokens)
            connection.encrypted_credentials = encryption_service.encrypt_credentials(credentials)
            connection.updated_at = datetime.now(timezone.utc)
            db.commit()
        
        return credentials["access_token"]
    
    def refresh_activities(self, user_id: int, connection: DataConnection, db: Session) -> int:
        """
        Fetch recent activities from Strava and store them.
        
        Args:
            user_id: User ID
            connection: DataConnection object
            db: Database session
            
        Returns:
            Number of activities processed
        """
        access_token = self.get_valid_access_token(connection, db)
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Fetch activities from last 30 days
        after = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
        
        url = f"{STRAVA_API_BASE}/athlete/activities"
        params = {"after": after, "per_page": 50}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        activities = response.json()
        count = 0
        
        for activity in activities:
            # Check if activity already exists
            existing = db.query(StravaActivity).filter(
                StravaActivity.user_id == user_id,
                StravaActivity.strava_activity_id == str(activity["id"])
            ).first()
            
            if not existing:
                # Extract metrics
                metrics = {
                    "distance": activity.get("distance"),
                    "duration": activity.get("moving_time"),
                    "elevation_gain": activity.get("total_elevation_gain"),
                    "average_speed": activity.get("average_speed"),
                    "max_speed": activity.get("max_speed"),
                    "average_power": activity.get("average_watts"),
                    "max_power": activity.get("max_watts"),
                    "average_heartrate": activity.get("average_heartrate"),
                    "max_heartrate": activity.get("max_heartrate"),
                    "calories": activity.get("calories")
                }
                
                strava_activity = StravaActivity(
                    user_id=user_id,
                    strava_activity_id=str(activity["id"]),
                    activity_name=activity["name"],
                    activity_type=activity["type"],
                    activity_date=datetime.fromisoformat(
                        activity["start_date"].replace("Z", "+00:00")
                    ),
                    metrics=json.dumps(metrics)
                )
                
                db.add(strava_activity)
                count += 1
        
        db.commit()
        logger.info(f"Imported {count} new Strava activities for user {user_id}")
        
        return count


class OuraService:
    """Service for Oura API integration."""
    
    def validate_token(self, token: str) -> bool:
        """
        Validate an Oura Personal Access Token.
        
        Args:
            token: Personal Access Token
            
        Returns:
            True if valid, False otherwise
        """
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{OURA_API_BASE}/personal_info"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Oura token validation failed: {str(e)}")
            return False
    
    def refresh_readiness_data(self, user_id: int, connection: DataConnection, db: Session) -> int:
        """
        Fetch readiness and HRV data from Oura.
        
        Args:
            user_id: User ID
            connection: DataConnection object
            db: Database session
            
        Returns:
            Number of records processed
        """
        encryption_service = get_encryption_service()
        credentials = encryption_service.decrypt_credentials(connection.encrypted_credentials)
        token = credentials["personal_access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Fetch data from last 30 days
        start_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        end_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Fetch readiness data
        url = f"{OURA_API_BASE}/daily_readiness"
        params = {"start_date": start_date, "end_date": end_date}
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        count = 0
        
        for day in data.get("data", []):
            day_date = datetime.fromisoformat(day["day"]).replace(tzinfo=timezone.utc)
            
            # Check if data already exists
            existing = db.query(OuraData).filter(
                OuraData.user_id == user_id,
                OuraData.data_date == day_date
            ).first()
            
            if existing:
                # Update existing record
                existing.readiness_score = day.get("score")
                existing.hrv_metrics = json.dumps({
                    "hrv_balance": day.get("contributors", {}).get("hrv_balance"),
                    "recovery_index": day.get("contributors", {}).get("recovery_index"),
                    "temperature_deviation": day.get("contributors", {}).get("temperature_deviation"),
                    "resting_heart_rate": day.get("contributors", {}).get("resting_heart_rate")
                })
                existing.raw_data = json.dumps(day)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Create new record
                oura_data = OuraData(
                    user_id=user_id,
                    data_date=day_date,
                    readiness_score=day.get("score"),
                    hrv_metrics=json.dumps({
                        "hrv_balance": day.get("contributors", {}).get("hrv_balance"),
                        "recovery_index": day.get("contributors", {}).get("recovery_index"),
                        "temperature_deviation": day.get("contributors", {}).get("temperature_deviation"),
                        "resting_heart_rate": day.get("contributors", {}).get("resting_heart_rate")
                    }),
                    raw_data=json.dumps(day)
                )
                db.add(oura_data)
            
            count += 1
        
        db.commit()
        logger.info(f"Imported {count} Oura readiness records for user {user_id}")
        
        return count


class AppleHealthService:
    """Service for Apple Health data processing."""
    
    def process_export(
        self, 
        file_content: bytes, 
        filename: str,
        user_id: int,
        db: Session
    ) -> Tuple[str, int]:
        """
        Process Apple Health export file.
        
        Args:
            file_content: File content bytes
            filename: Original filename
            user_id: User ID
            db: Database session
            
        Returns:
            Tuple of (upload_batch_id, record_count)
        """
        batch_id = str(uuid.uuid4())
        
        # Handle ZIP files
        if filename.endswith('.zip'):
            xml_content = self._extract_xml_from_zip(file_content)
        else:
            xml_content = file_content
        
        # Parse XML
        records = self._parse_health_xml(xml_content)
        
        # Aggregate by date
        daily_data = self._aggregate_by_date(records)
        
        # Store in database
        count = 0
        for date, metrics in daily_data.items():
            existing = db.query(AppleHealthData).filter(
                AppleHealthData.user_id == user_id,
                AppleHealthData.data_date == date
            ).first()
            
            if existing:
                # Update existing record
                existing.daily_metrics = json.dumps(metrics)
                existing.upload_batch_id = batch_id
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Create new record
                health_data = AppleHealthData(
                    user_id=user_id,
                    data_date=date,
                    daily_metrics=json.dumps(metrics),
                    upload_batch_id=batch_id
                )
                db.add(health_data)
            
            count += 1
        
        db.commit()
        logger.info(f"Processed {count} days of Apple Health data for user {user_id}")
        
        return batch_id, count
    
    def _extract_xml_from_zip(self, zip_content: bytes) -> bytes:
        """Extract export.xml from ZIP file."""
        with zipfile.ZipFile(BytesIO(zip_content)) as zf:
            # Look for export.xml or Export.xml
            for name in zf.namelist():
                if name.lower().endswith('export.xml'):
                    return zf.read(name)
        
        raise ValueError("No export.xml found in ZIP file")
    
    def _parse_health_xml(self, xml_content: bytes) -> list:
        """Parse Apple Health XML export."""
        root = ET.fromstring(xml_content)
        
        records = []
        for record in root.findall('.//Record'):
            record_type = record.get('type', '')
            value = record.get('value', '')
            start_date = record.get('startDate', '')
            
            # Parse date
            try:
                date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                continue
            
            records.append({
                'type': record_type,
                'value': value,
                'date': date
            })
        
        return records
    
    def _aggregate_by_date(self, records: list) -> dict:
        """Aggregate health records by date."""
        daily_data = {}
        
        for record in records:
            date = record['date'].replace(hour=0, minute=0, second=0, microsecond=0)
            
            if date not in daily_data:
                daily_data[date] = {
                    'steps': 0,
                    'distance': 0.0,
                    'active_energy': 0.0,
                    'resting_heart_rate': None,
                    'hrv': None,
                    'sleep_hours': None
                }
            
            # Map record types to metrics
            record_type = record['type']
            value = record['value']
            
            try:
                if 'StepCount' in record_type:
                    daily_data[date]['steps'] += int(float(value))
                elif 'DistanceWalkingRunning' in record_type:
                    daily_data[date]['distance'] += float(value)
                elif 'ActiveEnergyBurned' in record_type:
                    daily_data[date]['active_energy'] += float(value)
                elif 'RestingHeartRate' in record_type:
                    daily_data[date]['resting_heart_rate'] = int(float(value))
                elif 'HeartRateVariabilitySDNN' in record_type:
                    daily_data[date]['hrv'] = float(value)
                elif 'SleepAnalysis' in record_type:
                    # This is simplified - real implementation would need more logic
                    pass
            except (ValueError, TypeError):
                continue
        
        return daily_data


# Global service instances
_strava_service = None
_oura_service = None
_apple_health_service = None


def get_strava_service() -> StravaService:
    """Get or create Strava service singleton."""
    global _strava_service
    if _strava_service is None:
        _strava_service = StravaService()
    return _strava_service


def get_oura_service() -> OuraService:
    """Get or create Oura service singleton."""
    global _oura_service
    if _oura_service is None:
        _oura_service = OuraService()
    return _oura_service


def get_apple_health_service() -> AppleHealthService:
    """Get or create Apple Health service singleton."""
    global _apple_health_service
    if _apple_health_service is None:
        _apple_health_service = AppleHealthService()
    return _apple_health_service
