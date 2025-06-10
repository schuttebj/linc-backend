"""
LINC Automatic Endpoint Monitoring API
Real-time endpoint health monitoring and logging
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
import structlog
import json

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import get_current_user
from app.services.audit import AuditService, UserContext, AuditLogData
from app.models.user import User

logger = structlog.get_logger()
router = APIRouter()
settings = get_settings()

class EndpointMonitor:
    """Automatic endpoint health monitoring service"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"
        
        # Define all endpoints to monitor - Comprehensive list based on OpenAPI docs
        self.monitored_endpoints = [
            # Health endpoints (no auth)
            {"method": "GET", "path": "/", "auth_required": False, "category": "health"},
            {"method": "GET", "path": "/health", "auth_required": False, "category": "health"},
            {"method": "GET", "path": "/health/database", "auth_required": False, "category": "health"},
            
            # API Health endpoints
            {"method": "GET", "path": "/api/v1/health/", "auth_required": True, "category": "health"},
            {"method": "GET", "path": "/api/v1/health/detailed", "auth_required": True, "category": "health"},
            {"method": "GET", "path": "/api/v1/health/database", "auth_required": True, "category": "health"},
            
            # Authentication endpoints - GET only (no side effects)
            {"method": "GET", "path": "/api/v1/auth/me", "auth_required": True, "category": "auth"},
            {"method": "GET", "path": "/api/v1/auth/permissions", "auth_required": True, "category": "auth"},
            {"method": "GET", "path": "/api/v1/auth/roles", "auth_required": True, "category": "auth"},
            
            # User management endpoints - GET only (safe to test)
            {"method": "GET", "path": "/api/v1/users/", "auth_required": True, "category": "users"},
            {"method": "GET", "path": "/api/v1/users/roles/", "auth_required": True, "category": "users"},
            {"method": "GET", "path": "/api/v1/users/permissions/", "auth_required": True, "category": "users"},
            
            # Country configuration endpoints
            {"method": "GET", "path": "/api/v1/countries/current", "auth_required": True, "category": "countries"},
            {"method": "GET", "path": "/api/v1/countries/modules", "auth_required": True, "category": "countries"},
            {"method": "GET", "path": "/api/v1/countries/license-types", "auth_required": True, "category": "countries"},
            {"method": "GET", "path": "/api/v1/countries/printing-config", "auth_required": True, "category": "countries"},
            {"method": "GET", "path": "/api/v1/countries/fees", "auth_required": True, "category": "countries"},
            
            # Person management endpoints - GET and lookup endpoints only
            {"method": "GET", "path": "/api/v1/persons/", "auth_required": True, "category": "persons"},
            {"method": "POST", "path": "/api/v1/persons/search", "auth_required": True, "category": "persons"},
            {"method": "GET", "path": "/api/v1/persons/statistics/summary", "auth_required": True, "category": "persons"},
            {"method": "GET", "path": "/api/v1/persons/lookups/person-natures", "auth_required": True, "category": "persons"},
            {"method": "GET", "path": "/api/v1/persons/lookups/id-document-types", "auth_required": True, "category": "persons"},
            {"method": "GET", "path": "/api/v1/persons/lookups/address-types", "auth_required": True, "category": "persons"},
            
            # License management endpoints - GET only
            {"method": "GET", "path": "/api/v1/licenses/applications", "auth_required": True, "category": "licenses"},
            {"method": "GET", "path": "/api/v1/licenses/test-centers", "auth_required": True, "category": "licenses"},
            {"method": "GET", "path": "/api/v1/licenses/license-types", "auth_required": True, "category": "licenses"},
            {"method": "GET", "path": "/api/v1/licenses/application-statuses", "auth_required": True, "category": "licenses"},
            
            # File storage endpoints - GET only (safe to test)
            {"method": "GET", "path": "/api/v1/files/storage/metrics", "auth_required": True, "category": "files"},
            {"method": "GET", "path": "/api/v1/files/storage/health", "auth_required": True, "category": "files"},
            {"method": "GET", "path": "/api/v1/files/storage/largest-files", "auth_required": True, "category": "files"},
            
            # Monitoring endpoints (self-test)
            {"method": "GET", "path": "/api/v1/monitoring/health/endpoints", "auth_required": True, "category": "monitoring"},
            {"method": "GET", "path": "/api/v1/monitoring/health/uptime-report", "auth_required": True, "category": "monitoring"},
            {"method": "GET", "path": "/api/v1/monitoring/health/history?hours=1", "auth_required": True, "category": "monitoring"},
            
            # Admin endpoints - GET only (safe to test)
            {"method": "GET", "path": "/api/v1/admin/database/check-tables", "auth_required": True, "category": "admin"},
            {"method": "GET", "path": "/api/v1/admin/system/info", "auth_required": True, "category": "admin"}
        ]
    
    async def check_endpoint(self, session: aiohttp.ClientSession, endpoint: Dict[str, Any], 
                           auth_header: Optional[str] = None, include_response_data: bool = False) -> Dict[str, Any]:
        """Check a single endpoint with optional detailed response data"""
        url = f"{self.base_url}{endpoint['path']}"
        headers = {"User-Agent": "LINC-Monitor/1.0"}
        
        if endpoint["auth_required"] and auth_header:
            headers["Authorization"] = auth_header
        
        start_time = time.time()
        try:
            async with session.request(
                endpoint["method"], 
                url, 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as response:
                duration = (time.time() - start_time) * 1000
                
                # Get response data
                response_data = None
                response_text = None
                
                try:
                    response_text = await response.text()
                    if response_text:
                        response_data = json.loads(response_text)
                except json.JSONDecodeError:
                    response_data = response_text
                except Exception:
                    response_data = "Unable to parse response"
                
                result = {
                    "endpoint": endpoint["path"],
                    "method": endpoint["method"],
                    "category": endpoint["category"],
                    "status": "healthy" if 200 <= response.status < 400 else "unhealthy",
                    "status_code": response.status,
                    "response_time_ms": round(duration, 2),
                    "error": None,
                    "checked_at": datetime.utcnow().isoformat()
                }
                
                # Include detailed response data for development testing
                if include_response_data:
                    result.update({
                        "response_headers": dict(response.headers),
                        "response_data": response_data,
                        "response_size_bytes": len(response_text) if response_text else 0
                    })
                
                return result
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "category": endpoint["category"],
                "status": "error",
                "status_code": None,
                "response_time_ms": round(duration, 2),
                "error": str(e),
                "checked_at": datetime.utcnow().isoformat(),
                "response_data": None if not include_response_data else f"Connection error: {str(e)}"
            }
    
    async def monitor_all_endpoints(self, auth_header: Optional[str] = None, include_response_data: bool = False) -> Dict[str, Any]:
        """Monitor all endpoints and return comprehensive health report"""
        start_time = datetime.utcnow()
        
        async with aiohttp.ClientSession() as session:
            # Check all endpoints concurrently
            tasks = [
                self.check_endpoint(session, endpoint, auth_header, include_response_data)
                for endpoint in self.monitored_endpoints
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        endpoint_results = []
        for result in results:
            if isinstance(result, Exception):
                endpoint_results.append({
                    "status": "error",
                    "error": str(result),
                    "checked_at": datetime.utcnow().isoformat()
                })
            else:
                endpoint_results.append(result)
        
        # Calculate summary statistics
        healthy_count = len([r for r in endpoint_results if r.get("status") == "healthy"])
        unhealthy_count = len([r for r in endpoint_results if r.get("status") == "unhealthy"])
        error_count = len([r for r in endpoint_results if r.get("status") == "error"])
        total_count = len(endpoint_results)
        
        # Group by category
        categories = {}
        for result in endpoint_results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = {"healthy": 0, "unhealthy": 0, "error": 0, "total": 0}
            
            categories[category]["total"] += 1
            if result.get("status") == "healthy":
                categories[category]["healthy"] += 1
            elif result.get("status") == "unhealthy":
                categories[category]["unhealthy"] += 1
            else:
                categories[category]["error"] += 1
        
        # Overall system health
        health_percentage = (healthy_count / total_count * 100) if total_count > 0 else 0
        overall_status = "healthy" if health_percentage >= 90 else "degraded" if health_percentage >= 70 else "unhealthy"
        
        end_time = datetime.utcnow()
        
        # Separate successful and problematic endpoints
        successful_endpoints = [r for r in endpoint_results if r.get("status") == "healthy"]
        problematic_endpoints = [r for r in endpoint_results if r.get("status") in ["unhealthy", "error"]]
        
        return {
            "monitoring_summary": {
                "overall_status": overall_status,
                "health_percentage": round(health_percentage, 2),
                "total_endpoints": total_count,
                "healthy_endpoints": healthy_count,
                "unhealthy_endpoints": unhealthy_count,
                "error_endpoints": error_count,
                "monitoring_duration_ms": round((end_time - start_time).total_seconds() * 1000, 2),
                "monitored_at": start_time.isoformat()
            },
            "category_health": categories,
            "successful_endpoints": successful_endpoints,
            "problematic_endpoints": problematic_endpoints,
            "endpoint_details": endpoint_results,
            "alerts": problematic_endpoints
        }

# Notification service for production monitoring
class NotificationService:
    """Handle notifications for monitoring alerts"""
    
    @staticmethod
    async def send_alert(alert_data: Dict[str, Any], audit_service: AuditService, notification_type: str = "endpoint_failure"):
        """Send notification for monitoring alerts"""
        try:
            # Log notification attempt
            system_context = UserContext(
                user_id="system",
                username="notification_service",
                ip_address="127.0.0.1"
            )
            
            audit_service.log_action(AuditLogData(
                action_type="NOTIFICATION_SENT",
                entity_type="SYSTEM",
                entity_id=notification_type,
                success=True,
                new_values={
                    "notification_type": notification_type,
                    "alert_count": alert_data.get("alert_count", 0),
                    "overall_status": alert_data.get("overall_status"),
                    "health_percentage": alert_data.get("health_percentage")
                },
                **system_context.dict()
            ))
            
            logger.info(
                "Monitoring alert notification sent",
                notification_type=notification_type,
                alert_count=alert_data.get("alert_count", 0),
                overall_status=alert_data.get("overall_status")
            )
            
            # TODO: Implement actual notification methods (email, SMS, Slack, etc.)
            # For now, we're just logging the alert
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

# Global monitor instance
monitor = EndpointMonitor("http://localhost:8000")
notification_service = NotificationService()

# DEVELOPMENT ENDPOINT - Comprehensive testing with detailed responses
@router.get("/development/test-all")
async def development_test_all_endpoints(
    request: Request,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(lambda db=Depends(get_db): AuditService(db, settings.COUNTRY_CODE))
):
    """
    DEVELOPMENT ONLY: Comprehensive endpoint testing with detailed response data
    This endpoint tests all API calls and returns detailed success/failure information
    including full response data for debugging purposes.
    """
    try:
        # Update monitor base URL based on request
        host = request.headers.get("host", "localhost:8000")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        base_url = f"{scheme}://{host}"
        
        # Create monitor for current environment
        current_monitor = EndpointMonitor(base_url)
        
        # Use current user's auth for testing
        auth_header = request.headers.get("authorization")
        
        # Run comprehensive monitoring with detailed response data
        monitoring_result = await current_monitor.monitor_all_endpoints(auth_header, include_response_data=True)
        
        # Log development testing activity
        user_context = UserContext(
            user_id=str(current_user.id),
            username=current_user.username,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=request.headers.get("x-session-id")
        )
        
        audit_service.log_action(AuditLogData(
            action_type="DEVELOPMENT_ENDPOINT_TEST",
            entity_type="SYSTEM",
            entity_id="comprehensive_endpoint_test",
            success=True,
            new_values={
                "overall_status": monitoring_result["monitoring_summary"]["overall_status"],
                "health_percentage": monitoring_result["monitoring_summary"]["health_percentage"],
                "total_endpoints": monitoring_result["monitoring_summary"]["total_endpoints"],
                "problematic_count": len(monitoring_result["problematic_endpoints"]),
                "successful_count": len(monitoring_result["successful_endpoints"])
            },
            **user_context.dict()
        ))
        
        return {
            "success": True,
            "test_type": "development_comprehensive",
            "data": {
                "summary": monitoring_result["monitoring_summary"],
                "category_health": monitoring_result["category_health"],
                "successful_endpoints": monitoring_result["successful_endpoints"],
                "problematic_endpoints": monitoring_result["problematic_endpoints"],
                "detailed_responses": monitoring_result["endpoint_details"]
            },
            "message": f"Tested {monitoring_result['monitoring_summary']['total_endpoints']} endpoints. " +
                      f"Success: {len(monitoring_result['successful_endpoints'])}, " +
                      f"Problems: {len(monitoring_result['problematic_endpoints'])}"
        }
        
    except Exception as e:
        logger.error(f"Development endpoint testing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to run comprehensive endpoint testing")

# PRODUCTION ENDPOINTS - Standard monitoring and production features

@router.get("/health/endpoints")
async def monitor_endpoint_health(
    request: Request,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(lambda db=Depends(get_db): AuditService(db, settings.COUNTRY_CODE))
):
    """
    Monitor all endpoints and return health status
    This endpoint automatically tests all other endpoints and logs the results
    """
    try:
        # Update monitor base URL based on request
        host = request.headers.get("host", "localhost:8000")
        scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
        base_url = f"{scheme}://{host}"
        
        # Create monitor for current environment
        current_monitor = EndpointMonitor(base_url)
        
        # Use current user's auth for testing
        auth_header = request.headers.get("authorization")
        
        # Run monitoring
        monitoring_result = await current_monitor.monitor_all_endpoints(auth_header)
        
        # Log monitoring activity
        user_context = UserContext(
            user_id=str(current_user.id),
            username=current_user.username,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            session_id=request.headers.get("x-session-id")
        )
        
        audit_service.log_action(AuditLogData(
            action_type="ENDPOINT_MONITORING",
            entity_type="SYSTEM",
            entity_id="endpoint_health_check",
            success=True,
            new_values={
                "overall_status": monitoring_result["monitoring_summary"]["overall_status"],
                "health_percentage": monitoring_result["monitoring_summary"]["health_percentage"],
                "total_endpoints": monitoring_result["monitoring_summary"]["total_endpoints"],
                "alerts_count": len(monitoring_result["alerts"])
            },
            **user_context.dict()
        ))
        
        return {
            "success": True,
            "data": monitoring_result,
            "message": f"Monitored {monitoring_result['monitoring_summary']['total_endpoints']} endpoints"
        }
        
    except Exception as e:
        logger.error(f"Endpoint monitoring failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to monitor endpoints")

@router.post("/health/endpoints/continuous")
async def start_continuous_monitoring(
    background_tasks: BackgroundTasks,
    interval_minutes: int = 60,  # Default to hourly
    notification_threshold: int = 2,  # Send notification after 2 consecutive failures
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start continuous endpoint monitoring with notifications (admin only)
    This will automatically test all endpoints every N minutes and send notifications for issues
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Add background task for continuous monitoring with notifications
    background_tasks.add_task(
        continuous_endpoint_monitoring_with_notifications,
        interval_minutes=interval_minutes,
        notification_threshold=notification_threshold,
        db=db
    )
    
    return {
        "success": True,
        "message": f"Started continuous endpoint monitoring every {interval_minutes} minutes with notification threshold of {notification_threshold} failures",
        "interval_minutes": interval_minutes,
        "notification_threshold": notification_threshold
    }

async def continuous_endpoint_monitoring_with_notifications(
    interval_minutes: int, 
    notification_threshold: int,
    db: Session
):
    """Background task for continuous endpoint monitoring with notifications"""
    monitor = EndpointMonitor("http://localhost:8000")  # Use localhost for internal monitoring
    audit_service = AuditService(db, settings.COUNTRY_CODE)
    
    consecutive_failures = 0
    
    while True:
        try:
            # Run monitoring
            monitoring_result = await monitor.monitor_all_endpoints()
            
            # Check if system is unhealthy
            is_healthy = monitoring_result["monitoring_summary"]["overall_status"] == "healthy"
            has_alerts = len(monitoring_result["alerts"]) > 0
            
            if not is_healthy or has_alerts:
                consecutive_failures += 1
            else:
                consecutive_failures = 0
            
            # Log results to audit system
            system_context = UserContext(
                user_id="system",
                username="endpoint_monitor",
                ip_address="127.0.0.1"
            )
            
            audit_service.log_action(AuditLogData(
                action_type="CONTINUOUS_MONITORING",
                entity_type="SYSTEM",
                entity_id="background_health_check",
                success=True,
                new_values={
                    "overall_status": monitoring_result["monitoring_summary"]["overall_status"],
                    "health_percentage": monitoring_result["monitoring_summary"]["health_percentage"],
                    "unhealthy_endpoints": monitoring_result["monitoring_summary"]["unhealthy_endpoints"],
                    "error_endpoints": monitoring_result["monitoring_summary"]["error_endpoints"],
                    "consecutive_failures": consecutive_failures
                },
                **system_context.dict()
            ))
            
            # Send notification if threshold reached
            if consecutive_failures >= notification_threshold:
                await notification_service.send_alert({
                    "overall_status": monitoring_result["monitoring_summary"]["overall_status"],
                    "health_percentage": monitoring_result["monitoring_summary"]["health_percentage"],
                    "alert_count": len(monitoring_result["alerts"]),
                    "consecutive_failures": consecutive_failures,
                    "problematic_endpoints": monitoring_result["alerts"]
                }, audit_service, "continuous_monitoring_alert")
            
            # Log alerts for unhealthy endpoints
            for alert in monitoring_result["alerts"]:
                audit_service.log_security_event(
                    "endpoint_health_alert",
                    f"Endpoint {alert['endpoint']} is {alert['status']}: {alert.get('error', 'Status code: ' + str(alert.get('status_code')))}",
                    system_context,
                    severity="HIGH" if alert['status'] == "error" else "MEDIUM"
                )
            
            logger.info(
                "Continuous endpoint monitoring completed",
                overall_status=monitoring_result["monitoring_summary"]["overall_status"],
                health_percentage=monitoring_result["monitoring_summary"]["health_percentage"],
                alerts=len(monitoring_result["alerts"]),
                consecutive_failures=consecutive_failures
            )
            
        except Exception as e:
            consecutive_failures += 1
            logger.error(f"Continuous monitoring failed: {e}")
            
            # Log monitoring failure
            audit_service.log_action(AuditLogData(
                action_type="MONITORING_FAILURE",
                entity_type="SYSTEM",
                entity_id="background_health_check",
                success=False,
                error_message=str(e),
                **system_context.dict()
            ))
        
        # Wait for next check
        await asyncio.sleep(interval_minutes * 60)

@router.get("/health/uptime-report")
async def get_uptime_report(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(lambda db=Depends(get_db): AuditService(db, settings.COUNTRY_CODE))
):
    """Generate uptime monitoring report"""
    try:
        from sqlalchemy import func
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        end_time = datetime.utcnow()
        
        # Get monitoring logs from audit system
        from app.models.audit import AuditLog
        monitoring_logs = audit_service.db.query(AuditLog).filter(
            AuditLog.action_type.in_(["ENDPOINT_MONITORING", "CONTINUOUS_MONITORING"]),
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
            AuditLog.country_code == settings.COUNTRY_CODE
        ).order_by(AuditLog.timestamp.desc()).all()
        
        # Calculate uptime statistics
        total_checks = len(monitoring_logs)
        healthy_checks = len([log for log in monitoring_logs if log.new_values and log.new_values.get("overall_status") == "healthy"])
        
        uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 100
        
        # Group by hour for trend analysis
        hourly_stats = {}
        for log in monitoring_logs:
            hour_key = log.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly_stats:
                hourly_stats[hour_key] = {"total": 0, "healthy": 0}
            
            hourly_stats[hour_key]["total"] += 1
            if log.new_values and log.new_values.get("overall_status") == "healthy":
                hourly_stats[hour_key]["healthy"] += 1
        
        # Calculate hourly uptime percentages
        uptime_trend = []
        for hour, stats in sorted(hourly_stats.items()):
            hourly_uptime = (stats["healthy"] / stats["total"] * 100) if stats["total"] > 0 else 100
            uptime_trend.append({
                "hour": hour,
                "uptime_percentage": round(hourly_uptime, 2),
                "total_checks": stats["total"],
                "healthy_checks": stats["healthy"]
            })
        
        return {
            "success": True,
            "data": {
                "uptime_summary": {
                    "period_hours": hours,
                    "overall_uptime_percentage": round(uptime_percentage, 2),
                    "total_monitoring_checks": total_checks,
                    "healthy_checks": healthy_checks,
                    "unhealthy_checks": total_checks - healthy_checks,
                    "report_generated_at": datetime.utcnow().isoformat()
                },
                "uptime_trend": uptime_trend,
                "sla_status": {
                    "target_uptime": 99.0,  # 99% SLA target
                    "current_uptime": round(uptime_percentage, 2),
                    "sla_met": uptime_percentage >= 99.0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to generate uptime report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate uptime report")

@router.get("/health/history")
async def get_monitoring_history(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    audit_service: AuditService = Depends(lambda db=Depends(get_db): AuditService(db, settings.COUNTRY_CODE))
):
    """Get endpoint monitoring history from audit logs"""
    try:
        from datetime import timedelta
        
        start_time = datetime.utcnow() - timedelta(hours=hours)
        end_time = datetime.utcnow()
        
        # Get monitoring logs from audit system
        from app.models.audit import AuditLog
        monitoring_logs = audit_service.db.query(AuditLog).filter(
            AuditLog.action_type.in_(["ENDPOINT_MONITORING", "CONTINUOUS_MONITORING"]),
            AuditLog.timestamp >= start_time,
            AuditLog.timestamp <= end_time,
            AuditLog.country_code == settings.COUNTRY_CODE
        ).order_by(AuditLog.timestamp.desc()).all()
        
        history = []
        for log in monitoring_logs:
            history.append({
                "timestamp": log.timestamp.isoformat(),
                "overall_status": log.new_values.get("overall_status") if log.new_values else None,
                "health_percentage": log.new_values.get("health_percentage") if log.new_values else None,
                "total_endpoints": log.new_values.get("total_endpoints") if log.new_values else None,
                "alerts_count": log.new_values.get("alerts_count", 0) if log.new_values else 0,
                "success": log.success
            })
        
        return {
            "success": True,
            "data": {
                "history": history,
                "period_hours": hours,
                "total_checks": len(history)
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring history")

# LEGACY ENDPOINT - keeping for backward compatibility
async def continuous_endpoint_monitoring(interval_minutes: int, db: Session):
    """Legacy background task for continuous endpoint monitoring without notifications"""
    # Redirect to new function with default notification threshold
    await continuous_endpoint_monitoring_with_notifications(interval_minutes, 3, db) 