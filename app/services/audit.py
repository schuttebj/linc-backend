"""
LINC Comprehensive Audit Service
Complete transaction logging with old/new values tracking and fraud detection
Reference: linc-file-storage-audit.mdc requirements
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import uuid
import json
from dataclasses import dataclass, asdict
from pathlib import Path
import structlog
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.audit import AuditLog as AuditLogModel
from app.core.database import get_db
from app.services.file_storage import FileStorageService

logger = structlog.get_logger()

@dataclass
class UserContext:
    """User context for audit logging"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: str = "unknown"
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    location_id: Optional[str] = None
    
    def dict(self):
        return asdict(self)

@dataclass
class AuditLogData:
    """Data structure for audit log entries"""
    action_type: str
    entity_type: str
    entity_id: Optional[str] = None
    screen_reference: Optional[str] = None
    validation_codes: Optional[List[str]] = None
    business_rules_applied: Optional[List[str]] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    changed_fields: Optional[List[str]] = None
    files_created: Optional[List[str]] = None
    files_modified: Optional[List[str]] = None
    files_deleted: Optional[List[str]] = None
    execution_time_ms: Optional[int] = None
    database_queries: Optional[int] = None
    memory_usage_mb: Optional[int] = None
    success: bool = True
    error_message: Optional[str] = None
    warning_messages: Optional[List[str]] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: str = "unknown"
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    location_id: Optional[str] = None
    
    def dict(self):
        return asdict(self)

# AuditLogModel is imported from app.models.audit

class AuditService:
    """
    Comprehensive audit service for all system operations
    Provides fraud detection, compliance reporting, and security monitoring
    """
    
    def __init__(self, db_session: Session, country_code: str):
        self.db = db_session
        self.country_code = country_code.upper()
        self.file_storage = FileStorageService(country_code)
    
    def log_action(self, action_data: AuditLogData, transaction_id: Optional[str] = None) -> str:
        """
        Log any system action with comprehensive tracking
        Returns: transaction_id for correlation
        """
        if transaction_id is None:
            transaction_id = str(uuid.uuid4())
        
        try:
            # Create audit log entry
            audit_log = AuditLogModel(
                transaction_id=transaction_id,
                country_code=self.country_code,
                session_id=action_data.session_id,
                user_id=action_data.user_id,
                username=action_data.username,
                ip_address=action_data.ip_address,
                user_agent=action_data.user_agent,
                location_id=action_data.location_id,
                action_type=action_data.action_type,
                entity_type=action_data.entity_type,
                entity_id=action_data.entity_id,
                screen_reference=action_data.screen_reference,
                validation_codes=action_data.validation_codes,
                business_rules_applied=action_data.business_rules_applied,
                old_values=action_data.old_values,
                new_values=action_data.new_values,
                changed_fields=action_data.changed_fields,
                files_created=action_data.files_created,
                files_modified=action_data.files_modified,
                files_deleted=action_data.files_deleted,
                execution_time_ms=action_data.execution_time_ms,
                database_queries=action_data.database_queries,
                memory_usage_mb=action_data.memory_usage_mb,
                success=action_data.success,
                error_message=action_data.error_message,
                warning_messages=action_data.warning_messages,
                module_name=action_data.entity_type.lower(),
                system_version="1.0.0"
            )
            
            self.db.add(audit_log)
            self.db.commit()
            
            # Also write to file-based audit log for redundancy
            self._write_audit_file(audit_log)
            
            logger.info(
                "Audit log created",
                transaction_id=transaction_id,
                action=f"{action_data.action_type}:{action_data.entity_type}",
                user=action_data.username,
                success=action_data.success
            )
            
            return transaction_id
            
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            # Fallback to file-only logging if database fails
            self._write_audit_file_fallback(action_data, transaction_id)
            return transaction_id
    
    def log_data_change(self, entity_type: str, entity_id: str, 
                       old_data: Dict[str, Any], new_data: Dict[str, Any], 
                       user_context: UserContext, screen_reference: Optional[str] = None,
                       validation_codes: Optional[List[str]] = None) -> str:
        """
        Log data changes with old/new value tracking
        Critical for fraud detection and compliance
        """
        changed_fields = self._identify_changed_fields(old_data, new_data)
        
        audit_data = AuditLogData(
            action_type="UPDATE",
            entity_type=entity_type,
            entity_id=entity_id,
            screen_reference=screen_reference,
            validation_codes=validation_codes,
            old_values=old_data,
            new_values=new_data,
            changed_fields=changed_fields,
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_creation(self, entity_type: str, entity_id: str, 
                    entity_data: Dict[str, Any], user_context: UserContext,
                    screen_reference: Optional[str] = None,
                    validation_codes: Optional[List[str]] = None) -> str:
        """Log entity creation"""
        audit_data = AuditLogData(
            action_type="CREATE",
            entity_type=entity_type,
            entity_id=entity_id,
            screen_reference=screen_reference,
            validation_codes=validation_codes,
            new_values=entity_data,
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_deletion(self, entity_type: str, entity_id: str, 
                    entity_data: Dict[str, Any], user_context: UserContext,
                    screen_reference: Optional[str] = None) -> str:
        """Log entity deletion"""
        audit_data = AuditLogData(
            action_type="DELETE",
            entity_type=entity_type,
            entity_id=entity_id,
            screen_reference=screen_reference,
            old_values=entity_data,
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_view_access(self, entity_type: str, entity_id: str, 
                       user_context: UserContext, screen_reference: Optional[str] = None) -> str:
        """Log data access/viewing"""
        audit_data = AuditLogData(
            action_type="VIEW",
            entity_type=entity_type,
            entity_id=entity_id,
            screen_reference=screen_reference,
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_file_operation(self, operation: str, file_path: str, 
                          user_context: UserContext, metadata: Optional[Dict[str, Any]] = None,
                          entity_type: str = "FILE", entity_id: Optional[str] = None) -> str:
        """Log file operations for security and compliance"""
        
        files_data = {operation.lower(): [file_path]}
        
        audit_data = AuditLogData(
            action_type=f"FILE_{operation.upper()}",
            entity_type=entity_type,
            entity_id=entity_id or file_path,
            new_values=metadata or {"file_path": file_path},
            **{f"files_{operation.lower()}": [file_path] if operation.lower() in ['created', 'modified', 'deleted'] else None},
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_business_rule_application(self, rule_codes: List[str], entity_type: str, 
                                    entity_id: str, user_context: UserContext,
                                    validation_results: Optional[Dict[str, Any]] = None) -> str:
        """Log business rule applications for compliance tracking"""
        audit_data = AuditLogData(
            action_type="BUSINESS_RULE_VALIDATION",
            entity_type=entity_type,
            entity_id=entity_id,
            business_rules_applied=rule_codes,
            validation_codes=rule_codes,
            new_values=validation_results or {},
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def log_authentication(self, username: str, success: bool, ip_address: str,
                          user_agent: Optional[str] = None, error_message: Optional[str] = None) -> str:
        """Log authentication attempts"""
        audit_data = AuditLogData(
            action_type="AUTHENTICATION",
            entity_type="USER",
            entity_id=username,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        return self.log_action(audit_data)
    
    def log_security_event(self, event_type: str, description: str, 
                          user_context: UserContext, severity: str = "HIGH") -> str:
        """Log security events and potential fraud attempts"""
        audit_data = AuditLogData(
            action_type="SECURITY_EVENT",
            entity_type="SECURITY",
            entity_id=event_type,
            new_values={
                "event_type": event_type,
                "description": description,
                "severity": severity
            },
            **user_context.dict()
        )
        
        return self.log_action(audit_data)
    
    def _identify_changed_fields(self, old_data: Dict[str, Any], 
                               new_data: Dict[str, Any]) -> List[str]:
        """Identify which fields changed between old and new data"""
        changed_fields = []
        
        # Check all fields in new data
        for key, new_value in new_data.items():
            old_value = old_data.get(key)
            if old_value != new_value:
                changed_fields.append(key)
        
        # Check for removed fields
        for key in old_data.keys():
            if key not in new_data:
                changed_fields.append(key)
        
        return changed_fields
    
    def _write_audit_file(self, audit_log: AuditLogModel):
        """Write audit log to file for redundancy"""
        try:
            log_date = audit_log.timestamp.strftime('%Y%m%d')
            log_file = self.file_storage.base_path / f"audit/logs/{log_date}.log"
            
            log_entry = {
                "timestamp": audit_log.timestamp.isoformat(),
                "transaction_id": str(audit_log.transaction_id),
                "action": f"{audit_log.action_type}:{audit_log.entity_type}",
                "entity_id": audit_log.entity_id,
                "user": audit_log.username,
                "ip": audit_log.ip_address,
                "success": audit_log.success,
                "country": audit_log.country_code
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write audit file: {e}")
    
    def _write_audit_file_fallback(self, action_data: AuditLogData, transaction_id: str):
        """Fallback file logging when database is unavailable"""
        try:
            log_date = datetime.utcnow().strftime('%Y%m%d')
            log_file = self.file_storage.base_path / f"audit/logs/{log_date}_fallback.log"
            
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "transaction_id": transaction_id,
                "action": f"{action_data.action_type}:{action_data.entity_type}",
                "entity_id": action_data.entity_id,
                "user": action_data.username,
                "ip": action_data.ip_address,
                "success": action_data.success,
                "country": self.country_code,
                "fallback": True
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, default=str) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to write fallback audit file: {e}")
    
    def get_user_activity(self, user_id: str, start_date: datetime, 
                         end_date: datetime) -> List[Dict[str, Any]]:
        """Get user activity for a date range"""
        try:
            logs = self.db.query(AuditLogModel).filter(
                AuditLogModel.user_id == user_id,
                AuditLogModel.timestamp >= start_date,
                AuditLogModel.timestamp <= end_date,
                AuditLogModel.country_code == self.country_code
            ).order_by(AuditLogModel.timestamp.desc()).all()
            
            return [self._audit_log_to_dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error retrieving user activity: {e}")
            return []
    
    def get_entity_history(self, entity_type: str, entity_id: str) -> List[Dict[str, Any]]:
        """Get complete history for an entity"""
        try:
            logs = self.db.query(AuditLogModel).filter(
                AuditLogModel.entity_type == entity_type,
                AuditLogModel.entity_id == entity_id,
                AuditLogModel.country_code == self.country_code
            ).order_by(AuditLogModel.timestamp.desc()).all()
            
            return [self._audit_log_to_dict(log) for log in logs]
            
        except Exception as e:
            logger.error(f"Error retrieving entity history: {e}")
            return []
    
    def detect_suspicious_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Detect potentially suspicious activity patterns"""
        from datetime import timedelta
        
        try:
            start_time = datetime.utcnow() - timedelta(hours=hours)
            suspicious_patterns = []
            
            # Check for multiple failed authentication attempts
            failed_auths = self.db.query(AuditLogModel).filter(
                AuditLogModel.action_type == "AUTHENTICATION",
                AuditLogModel.success == False,
                AuditLogModel.timestamp >= start_time,
                AuditLogModel.country_code == self.country_code
            ).all()
            
            # Group by IP address and count failures
            failed_by_ip = {}
            for auth in failed_auths:
                ip = auth.ip_address
                failed_by_ip[ip] = failed_by_ip.get(ip, 0) + 1
            
            for ip, count in failed_by_ip.items():
                if count >= 5:  # 5 or more failed attempts
                    suspicious_patterns.append({
                        "type": "multiple_failed_authentications",
                        "ip_address": ip,
                        "count": count,
                        "severity": "HIGH" if count >= 10 else "MEDIUM"
                    })
            
            # Check for unusual data access patterns
            # Users accessing large amounts of data
            view_actions = self.db.query(AuditLogModel).filter(
                AuditLogModel.action_type == "VIEW",
                AuditLogModel.timestamp >= start_time,
                AuditLogModel.country_code == self.country_code
            ).all()
            
            views_by_user = {}
            for view in view_actions:
                user = view.username or "unknown"
                views_by_user[user] = views_by_user.get(user, 0) + 1
            
            for user, count in views_by_user.items():
                if count >= 100:  # More than 100 views in period
                    suspicious_patterns.append({
                        "type": "excessive_data_access",
                        "username": user,
                        "count": count,
                        "severity": "MEDIUM"
                    })
            
            return suspicious_patterns
            
        except Exception as e:
            logger.error(f"Error detecting suspicious activity: {e}")
            return []
    
    def _audit_log_to_dict(self, audit_log: AuditLogModel) -> Dict[str, Any]:
        """Convert audit log model to dictionary"""
        return {
            "id": str(audit_log.id),
            "transaction_id": str(audit_log.transaction_id),
            "timestamp": audit_log.timestamp.isoformat(),
            "action_type": audit_log.action_type,
            "entity_type": audit_log.entity_type,
            "entity_id": audit_log.entity_id,
            "username": audit_log.username,
            "ip_address": audit_log.ip_address,
            "success": audit_log.success,
            "old_values": audit_log.old_values,
            "new_values": audit_log.new_values,
            "changed_fields": audit_log.changed_fields,
            "validation_codes": audit_log.validation_codes,
            "error_message": audit_log.error_message
        }


class FraudDetectionService:
    """
    Advanced fraud detection based on audit logs
    """
    
    def __init__(self, audit_service: AuditService):
        self.audit_service = audit_service
    
    def analyze_user_patterns(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """Analyze user behavior patterns for anomalies"""
        from datetime import timedelta
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        activity = self.audit_service.get_user_activity(user_id, start_date, end_date)
        
        if not activity:
            return {"status": "no_data", "user_id": user_id}
        
        # Analyze patterns
        analysis = {
            "user_id": user_id,
            "period_days": days,
            "total_actions": len(activity),
            "unique_ips": len(set(log["ip_address"] for log in activity)),
            "failed_actions": sum(1 for log in activity if not log["success"]),
            "action_types": {},
            "suspicious_indicators": []
        }
        
        # Count action types
        for log in activity:
            action = log["action_type"]
            analysis["action_types"][action] = analysis["action_types"].get(action, 0) + 1
        
        # Check for suspicious patterns
        if analysis["unique_ips"] > 10:
            analysis["suspicious_indicators"].append("multiple_ip_addresses")
        
        if analysis["failed_actions"] > analysis["total_actions"] * 0.2:
            analysis["suspicious_indicators"].append("high_failure_rate")
        
        # Check for unusual activity times
        weekend_activity = sum(1 for log in activity 
                             if datetime.fromisoformat(log["timestamp"]).weekday() >= 5)
        if weekend_activity > analysis["total_actions"] * 0.5:
            analysis["suspicious_indicators"].append("excessive_weekend_activity")
        
        return analysis 