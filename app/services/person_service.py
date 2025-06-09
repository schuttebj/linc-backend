"""
Person Service
Business logic for person management operations
"""

from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import structlog

from app.models.person import Person, PersonAddress
from app.schemas.person import PersonCreateRequest, PersonSearchRequest
from app.core.database import get_db_context
from app.core.config import settings

logger = structlog.get_logger()


class PersonService:
    """Service class for person-related business operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_person(self, person_data: PersonCreateRequest) -> Person:
        """Create a new person record"""
        try:
            # Create person instance
            person = Person(
                first_name=person_data.first_name,
                middle_name=person_data.middle_name,
                surname=person_data.surname,
                date_of_birth=person_data.date_of_birth,
                gender=person_data.gender,
                identification_type=person_data.identification_type,
                identification_number=person_data.identification_number,
                nationality=person_data.nationality,
                email_address=person_data.email_address,
                phone_number=person_data.phone_number,
                country_code=settings.COUNTRY_CODE
            )
            
            self.db.add(person)
            self.db.flush()  # To get the ID
            
            # Create address if provided
            if person_data.address:
                address = PersonAddress(
                    person_id=person.id,
                    address_type="PRIMARY",
                    street_address=person_data.address.street_address,
                    suburb=person_data.address.suburb,
                    city=person_data.address.city,
                    province=person_data.address.province,
                    postal_code=person_data.address.postal_code,
                    country_code=settings.COUNTRY_CODE
                )
                self.db.add(address)
            
            self.db.commit()
            self.db.refresh(person)
            
            return person
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating person: {e}")
            raise
    
    async def get_by_id(self, person_id: str) -> Optional[Person]:
        """Get person by ID"""
        try:
            return self.db.query(Person).filter(
                and_(
                    Person.id == person_id,
                    Person.country_code == settings.COUNTRY_CODE,
                    Person.is_deleted == False
                )
            ).first()
        except Exception as e:
            logger.error(f"Error getting person by ID {person_id}: {e}")
            raise
    
    async def find_by_identification(
        self, 
        identification_type: str, 
        identification_number: str
    ) -> Optional[Person]:
        """Find person by identification details"""
        try:
            return self.db.query(Person).filter(
                and_(
                    Person.identification_type == identification_type,
                    Person.identification_number == identification_number,
                    Person.country_code == settings.COUNTRY_CODE,
                    Person.is_deleted == False
                )
            ).first()
        except Exception as e:
            logger.error(f"Error finding person by identification: {e}")
            raise
    
    async def search_persons(
        self, 
        search_request: PersonSearchRequest, 
        page: int = 1, 
        page_size: int = 20
    ) -> Tuple[List[Person], int]:
        """Search persons with pagination"""
        try:
            query = self.db.query(Person).filter(
                and_(
                    Person.country_code == settings.COUNTRY_CODE,
                    Person.is_deleted == False
                )
            )
            
            # Apply search filters
            if search_request.identification_type:
                query = query.filter(Person.identification_type == search_request.identification_type)
            
            if search_request.identification_number:
                query = query.filter(Person.identification_number.ilike(f"%{search_request.identification_number}%"))
            
            if search_request.first_name:
                query = query.filter(Person.first_name.ilike(f"%{search_request.first_name}%"))
            
            if search_request.surname:
                query = query.filter(Person.surname.ilike(f"%{search_request.surname}%"))
            
            if search_request.date_of_birth:
                query = query.filter(Person.date_of_birth == search_request.date_of_birth)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * page_size
            persons = query.offset(offset).limit(page_size).all()
            
            return persons, total_count
            
        except Exception as e:
            logger.error(f"Error searching persons: {e}")
            raise
    
    async def update_person(self, person_id: str, person_data: PersonCreateRequest) -> Optional[Person]:
        """Update person record"""
        try:
            person = await self.get_by_id(person_id)
            if not person:
                return None
            
            # Update fields
            person.first_name = person_data.first_name
            person.middle_name = person_data.middle_name
            person.surname = person_data.surname
            person.date_of_birth = person_data.date_of_birth
            person.gender = person_data.gender
            person.identification_type = person_data.identification_type
            person.identification_number = person_data.identification_number
            person.nationality = person_data.nationality
            person.email_address = person_data.email_address
            person.phone_number = person_data.phone_number
            
            self.db.commit()
            self.db.refresh(person)
            
            return person
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating person {person_id}: {e}")
            raise
    
    async def delete_person(self, person_id: str) -> bool:
        """Soft delete person record"""
        try:
            person = await self.get_by_id(person_id)
            if not person:
                return False
            
            person.is_deleted = True
            self.db.commit()
            
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting person {person_id}: {e}")
            raise 