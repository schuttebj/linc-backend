"""
Universal Enums for LINC System
These enums represent states/statuses that are consistent across all countries
"""

from enum import Enum

# ============================================================================
# UNIVERSAL ENUMS - Based on Refactored Documentation Analysis
# These represent standardized values that are consistent across countries
# ============================================================================

class Gender(Enum):
    """Universal gender codes - consistent across all countries"""
    MALE = "01"
    FEMALE = "02"

class ValidationStatus(Enum):
    """Universal validation states for person records"""
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"
    EXPIRED = "expired"

class ApplicationStatus(Enum):
    """Universal application workflow states - from Screen Field Specifications"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    APPROVED = "approved"
    LICENSE_PRODUCED = "license_produced"
    LICENSE_ISSUED = "license_issued"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

class LicenseStatus(Enum):
    """Universal license status codes"""
    VALID = "01"
    EXPIRED = "02"
    SUSPENDED = "03"
    CANCELLED = "04"
    REVOKED = "05"
    PROVISIONAL = "06"
    PENDING = "07"

class TransactionStatus(Enum):
    """Universal financial transaction states"""
    INITIATED = "1"
    PART_PAID = "2"
    PAID = "3"
    REMOVED = "4"
    CANCELLED = "5"

class AddressType(Enum):
    """Universal address categories"""
    RESIDENTIAL = "residential"
    POSTAL = "postal"
    BUSINESS = "business"
    TEMPORARY = "temporary"

class InfringementStatus(Enum):
    """Universal infringement notice statuses - from Business Rules"""
    ISSUED = "issued"
    PAID = "paid"
    UNPAID = "unpaid"
    COURT = "court"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    UNDER_REVIEW = "under_review"

class CourtVerdict(Enum):
    """Universal court verdict types"""
    GUILTY = "guilty"
    NOT_GUILTY = "not_guilty"
    DISMISSED = "dismissed"
    POSTPONED = "postponed"

class PaymentMethod(Enum):
    """Universal payment methods"""
    CASH = "cash"
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_PAYMENT = "mobile_payment"
    CHEQUE = "cheque"

class VehicleCondition(Enum):
    """Universal vehicle condition assessments - from Inspection Screen"""
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class InspectionResult(Enum):
    """Universal vehicle inspection results"""
    PASS = "pass"
    FAIL = "fail"
    CONDITIONAL = "conditional"

class PrDPCategory(Enum):
    """Universal Professional Driving Permit categories"""
    GOODS = "G"
    PASSENGERS = "P"
    DANGEROUS = "D"

class TestResult(Enum):
    """Universal driving test results"""
    PASS = "pass"
    FAIL = "fail"
    ABSENT = "absent"
    CANCELLED = "cancelled"

class CertificateStatus(Enum):
    """Universal certificate lifecycle status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    REVOKED = "revoked"

class AuditAction(Enum):
    """Universal audit action types - from Business Rules"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VIEW = "view"
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
    SUSPEND = "suspend"
    REINSTATE = "reinstate"

# ============================================================================
# COUNTRY-SPECIFIC CONFIGURATION PATTERNS
# These will be handled as strings with country-specific validation
# ============================================================================

"""
Country-Specific Fields (handled as strings with configuration):

1. ID_DOCUMENT_TYPES:
   - South Africa: ["RSA_ID", "RSA_PASSPORT", "TEMPORARY_ID", "ASYLUM_PERMIT"]
   - Kenya: ["NATIONAL_ID", "PASSPORT", "REFUGEE_ID", "ALIEN_ID"] 
   - Nigeria: ["NATIONAL_ID", "VOTERS_CARD", "DRIVERS_LICENSE", "PASSPORT"]

2. LICENSE_TYPES:
   - South Africa: ["A", "A1", "B", "C", "C1", "EB", "EC", "EC1"]
   - Kenya: ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]
   - Nigeria: ["A", "B", "C", "D", "E", "F"]

3. NATIONALITY_CODES:
   - ISO country codes with country-specific preferences
   - Local terminology variations

4. LANGUAGE_PREFERENCES:
   - South Africa: ["EN", "AF", "ZU", "XH", "ST", "TN", "SS", "VE", "TS", "NR", "ND"]
   - Kenya: ["EN", "SW", "KI", "LU", "KA", "ME", "GU", "KU", "MA", "TU"]
   - Nigeria: ["EN", "HA", "IG", "YO", "FU", "IJ", "KA", "TI", "UR", "BI"]

5. AUTHORITY_CODES:
   - Country-specific government departments and agencies
   - Regional/provincial variations

6. FEE_STRUCTURES:
   - Country-specific fee categories and amounts
   - Currency and tax variations

Configuration will be managed through:
- app/core/config.py: COUNTRY_CODE setting
- Country-specific configuration files
- Database lookup tables with country filters
- Validation rules that reference country configuration
"""

class NotificationStatus(str, Enum):
    """Notification status - universal"""
    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DISMISSED = "dismissed"


class PrintJobStatus(str, Enum):
    """Print job status - universal"""
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled" 