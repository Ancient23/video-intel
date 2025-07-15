"""
Technical Debt Tracking Model
"""
from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from beanie import Document
from pydantic import Field, BaseModel


class DebtSeverity(str, Enum):
    """Severity levels for technical debt items"""
    CRITICAL = "critical"      # Security vulnerabilities, data loss risks
    HIGH = "high"             # Core functionality blockers
    MEDIUM = "medium"         # Performance issues, missing features
    LOW = "low"               # Code quality, documentation
    

class DebtCategory(str, Enum):
    """Categories of technical debt"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    INCOMPLETE = "incomplete"
    HARDCODED = "hardcoded"
    MISSING_INTEGRATION = "missing_integration"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ERROR_HANDLING = "error_handling"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    

class DebtStatus(str, Enum):
    """Status of technical debt items"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DEFERRED = "deferred"
    WON_T_FIX = "won't_fix"


class TechnicalDebtItem(BaseModel):
    """Individual technical debt item"""
    id: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_numbers: Optional[List[int]] = None
    category: DebtCategory
    severity: DebtSeverity
    status: DebtStatus = DebtStatus.OPEN
    estimated_effort_hours: Optional[float] = None
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    related_issues: List[str] = Field(default_factory=list)  # GitHub issue IDs
    

class TechnicalDebt(Document):
    """MongoDB document for tracking technical debt"""
    
    project_name: str = Field(default="video-intelligence-platform")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Debt items grouped by component/service
    debt_items: Dict[str, List[TechnicalDebtItem]] = Field(default_factory=dict)
    
    # Summary statistics
    total_items: int = Field(default=0)
    open_items: int = Field(default=0)
    critical_items: int = Field(default=0)
    high_priority_items: int = Field(default=0)
    
    # Estimated total effort
    total_estimated_hours: float = Field(default=0.0)
    
    # Tags for filtering
    all_tags: List[str] = Field(default_factory=list)
    
    class Settings:
        name = "technical_debt"
        indexes = ["project_name"]
    
    def add_debt_item(
        self, 
        component: str,
        item: TechnicalDebtItem
    ):
        """Add a new technical debt item"""
        if component not in self.debt_items:
            self.debt_items[component] = []
        
        # Check if item with same ID already exists
        existing_ids = {debt.id for debt in self.debt_items[component]}
        if item.id not in existing_ids:
            self.debt_items[component].append(item)
            self._update_statistics()
    
    def update_debt_status(
        self,
        component: str,
        item_id: str,
        new_status: DebtStatus,
        resolution_notes: Optional[str] = None
    ):
        """Update the status of a debt item"""
        if component in self.debt_items:
            for item in self.debt_items[component]:
                if item.id == item_id:
                    item.status = new_status
                    item.updated_at = datetime.now(timezone.utc)
                    if new_status == DebtStatus.RESOLVED:
                        item.resolved_at = datetime.now(timezone.utc)
                        if resolution_notes:
                            item.resolution_notes = resolution_notes
                    self._update_statistics()
                    break
    
    def get_debt_by_severity(self, severity: DebtSeverity) -> List[TechnicalDebtItem]:
        """Get all debt items of a specific severity"""
        items = []
        for component_items in self.debt_items.values():
            items.extend([item for item in component_items if item.severity == severity])
        return items
    
    def get_debt_by_category(self, category: DebtCategory) -> List[TechnicalDebtItem]:
        """Get all debt items of a specific category"""
        items = []
        for component_items in self.debt_items.values():
            items.extend([item for item in component_items if item.category == category])
        return items
    
    def get_open_debt_items(self) -> List[TechnicalDebtItem]:
        """Get all open debt items"""
        items = []
        for component_items in self.debt_items.values():
            items.extend([item for item in component_items if item.status == DebtStatus.OPEN])
        return items
    
    def _update_statistics(self):
        """Update summary statistics"""
        all_items = []
        for component_items in self.debt_items.values():
            all_items.extend(component_items)
        
        self.total_items = len(all_items)
        self.open_items = sum(1 for item in all_items if item.status == DebtStatus.OPEN)
        self.critical_items = sum(1 for item in all_items if item.severity == DebtSeverity.CRITICAL)
        self.high_priority_items = sum(1 for item in all_items if item.severity == DebtSeverity.HIGH)
        
        # Calculate total estimated effort
        self.total_estimated_hours = sum(
            item.estimated_effort_hours or 0 
            for item in all_items 
            if item.status in [DebtStatus.OPEN, DebtStatus.IN_PROGRESS]
        )
        
        # Update all tags
        all_tags = set()
        for item in all_items:
            all_tags.update(item.tags)
        self.all_tags = sorted(list(all_tags))
        
        self.updated_at = datetime.now(timezone.utc)
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a technical debt report"""
        report = {
            "summary": {
                "total_items": self.total_items,
                "open_items": self.open_items,
                "critical_items": self.critical_items,
                "high_priority_items": self.high_priority_items,
                "estimated_hours_remaining": self.total_estimated_hours
            },
            "by_component": {},
            "by_severity": {
                "critical": [],
                "high": [],
                "medium": [],
                "low": []
            },
            "by_category": {},
            "recently_updated": []
        }
        
        # Group by component
        for component, items in self.debt_items.items():
            open_items = [item for item in items if item.status == DebtStatus.OPEN]
            if open_items:
                report["by_component"][component] = {
                    "open_items": len(open_items),
                    "total_hours": sum(item.estimated_effort_hours or 0 for item in open_items)
                }
        
        # Group by severity
        for item in self.get_open_debt_items():
            severity_key = item.severity.value
            report["by_severity"][severity_key].append({
                "id": item.id,
                "title": item.title,
                "component": self._find_component_for_item(item),
                "estimated_hours": item.estimated_effort_hours
            })
        
        # Group by category
        for category in DebtCategory:
            category_items = self.get_debt_by_category(category)
            open_category_items = [item for item in category_items if item.status == DebtStatus.OPEN]
            if open_category_items:
                report["by_category"][category.value] = len(open_category_items)
        
        # Recently updated items
        all_items = []
        for component, items in self.debt_items.items():
            for item in items:
                all_items.append((component, item))
        
        # Sort by update time and get top 10
        all_items.sort(key=lambda x: x[1].updated_at, reverse=True)
        report["recently_updated"] = [
            {
                "id": item.id,
                "title": item.title,
                "component": component,
                "status": item.status.value,
                "updated_at": item.updated_at.isoformat()
            }
            for component, item in all_items[:10]
        ]
        
        return report
    
    def _find_component_for_item(self, target_item: TechnicalDebtItem) -> Optional[str]:
        """Find which component contains a specific item"""
        for component, items in self.debt_items.items():
            if any(item.id == target_item.id for item in items):
                return component
        return None