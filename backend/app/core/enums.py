"""
Database ENUM types for Fleet SaaS.

Using Python Enum classes that map to PostgreSQL ENUM types.
This provides:
- Type safety in Python code
- Database-level validation
- Better performance than String columns
- Self-documenting code
"""

from enum import Enum


class UserRole(str, Enum):
    """
    User roles in the system.
    Inherits from str for JSON serialization compatibility.
    """
    SUPER_ADMIN = "super_admin"   # Can manage multiple tenants (this is for SaaS admin users, not tenant users)
    ADMIN = "admin"           # Full access to tenant
    MANAGER = "manager"       # Can manage fleet, orders, reports
    DISPATCHER = "dispatcher" # Can assign orders, manage trips
    DRIVER = "driver"         # Limited access, mobile app focused


class VehicleType(str, Enum):
    """Types of vehicles in the fleet."""
    TRUCK = "truck"
    VAN = "van"
    OTHER = "other"


class VehicleStatus(str, Enum):
    """
    Vehicle availability status.
    Controls whether vehicle can be assigned to trips.
    """
    AVAILABLE = "available"     # Ready to be assigned
    ON_ROUTE = "on_route"       # Currently on a trip
    MAINTENANCE = "maintenance" # In repair/service
    INACTIVE = "inactive"       # Decommissioned/sold
    RESERVED = "reserved"       # Reserved for a future trip

class TrailerType(str, Enum):
    """Types of trailers based on cargo requirements."""
    STANDARD = "standard"       # General cargo
    REFRIGERATED = "refrigerated" # Temperature controlled
    FLATBED = "flatbed"         # Open top for large items
    TANKER = "tanker"           # Liquid cargo


class TrailerStatus(str, Enum):
    """Trailer availability status."""
    AVAILABLE = "available"
    ATTACHED = "attached"       # Currently attached to a vehicle
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class WarehouseType(str, Enum):
    """
    Location types for logistics.
    Affects routing and scheduling logic.
    """
    WAREHOUSE = "warehouse"     # Company's own warehouse
    CLIENT = "client"           # Client's location
    PICKUP_POINT = "pickup_point" # Third-party pickup location


class OrderStatus(str, Enum):
    """
    Order lifecycle status.
    
    Flow: pending → assigned → in_transit → delivered
          └─────────────────→ cancelled (from any state)
    """
    PENDING = "pending"         # Waiting for assignment
    ASSIGNED = "assigned"       # Assigned to a trip, not started
    IN_TRANSIT = "in_transit"   # Currently being transported
    DELIVERED = "delivered"     # Successfully completed
    CANCELLED = "cancelled"     # Cancelled at any point
    FAILED = "failed"           # Failed during transit (e.g. accident)
    RETURNED = "returned"         # Returned to origin (e.g. refused delivery)


class TripStatus(str, Enum):
    """
    Trip lifecycle status.
    
    Flow: planned → in_progress → completed
          └──────────────────→ cancelled (from any state)
    """
    PLANNED = "planned"         # Scheduled but not started
    IN_PROGRESS = "in_progress" # Currently executing
    COMPLETED = "completed"     # Successfully finished
    CANCELLED = "cancelled"     # Cancelled


class WorkType(str, Enum):
    """
    Driver work time categories.
    Important for EU driving regulations (Regulation EC 561/2006).
    """
    DRIVING = "driving"   # Behind the wheel
    REST = "rest"         # Mandatory rest period
    AVAILABILITY = "availability" # Available but not driving (e.g. waiting for assignment)
    LOADING = "loading"   # Loading/unloading cargo
    WAITING = "waiting"   # Waiting at location
    BREAK = "break"         # Short break (not rest)
    OTHER = "other"       # Administrative, etc.
