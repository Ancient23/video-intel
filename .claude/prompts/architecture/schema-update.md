# MongoDB Schema Update Template

## Description
Plan and implement updates to MongoDB schemas while maintaining data integrity and backward compatibility.

## When to Use
- Adding new fields to existing collections
- Modifying field types or structures
- Creating new relationships between documents
- Optimizing indexes for performance
- Implementing new business requirements

## Prerequisites
- Understanding of current schema
- Clear requirements for changes
- Impact analysis completed
- Migration strategy planned

## Input Required
- **Collection**: Which collection to update
- **Changes**: What modifications needed
- **Reason**: Business or technical driver
- **Impact**: What code will be affected

## Pre-Update Analysis

### 1. Review Current Schema

```python
# Check current model definition
# services/backend/models/[collection].py

# Verify in MongoDB
from backend.models import [Model]
sample = await [Model].find_one()
print(sample.model_dump())
```

### 2. PRD Alignment

Verify changes align with PRD:
- Check `/docs/new/video-intelligence-prd.md`
- Ensure schema supports requirements
- Maintain architectural consistency

### 3. Impact Assessment

```bash
# Find all code using this model
grep -r "[ModelName]" services/backend/ --include="*.py"

# Check for direct field access
grep -r "\.[field_name]" services/backend/ --include="*.py"
```

## Schema Update Patterns

### 1. Adding New Fields

#### With Default Value
```python
class Video(Document):
    # Existing fields...
    
    # New field with default
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

#### With Migration Required
```python
# If no sensible default exists
processing_version: Optional[str] = Field(default=None)

# Create migration script
async def migrate_processing_version():
    async for video in Video.find_all():
        if video.processing_version is None:
            video.processing_version = "1.0"
            await video.save()
```

### 2. Modifying Field Types

#### Safe Type Changes
```python
# Before: Simple string
provider: str

# After: Enum with backward compatibility
provider: Union[ProviderType, str] = Field(...)

@field_validator('provider')
@classmethod
def validate_provider(cls, v):
    if isinstance(v, str):
        # Convert old string values
        return ProviderType(v)
    return v
```

#### Complex Type Changes
```python
# Before: Single value
scene_id: str

# After: List of values
scene_ids: List[str] = Field(default_factory=list)

@root_validator(pre=True)
@classmethod
def migrate_scene_id(cls, values):
    # Handle old single value
    if 'scene_id' in values and 'scene_ids' not in values:
        values['scene_ids'] = [values.pop('scene_id')]
    return values
```

### 3. Adding Relationships

#### One-to-Many
```python
class Video(Document):
    # Reference to many scenes
    scene_ids: List[PydanticObjectId] = Field(default_factory=list)
    
    async def get_scenes(self) -> List[Scene]:
        """Fetch related Scene documents"""
        return await Scene.find(In(Scene.id, self.scene_ids)).to_list()
```

#### Many-to-Many
```python
class Video(Document):
    tag_ids: List[PydanticObjectId] = Field(default_factory=list)

class Tag(Document):
    name: str
    video_ids: List[PydanticObjectId] = Field(default_factory=list)
```

### 4. Index Optimization

```python
class Settings:
    name = "videos"
    indexes = [
        IndexModel([("created_at", -1)]),
        IndexModel([("status", 1), ("created_at", -1)]),
        IndexModel([("title", TEXT)]),  # Text search
        IndexModel(
            [("user_id", 1), ("status", 1)],
            name="user_status_idx"
        ),
    ]
```

## Migration Strategy

### 1. Backward Compatible Changes

For adding fields with defaults:
```python
# No migration needed - Beanie handles it
# Just deploy new model
```

### 2. Simple Migration Script

```python
#!/usr/bin/env python3
"""Migrate [description]"""

import asyncio
from datetime import datetime, timezone
from backend.core.database import init_database, Database
from backend.models import [Model]

async def migrate():
    await init_database()
    
    try:
        count = 0
        async for doc in [Model].find_all():
            # Perform migration
            doc.new_field = calculate_value(doc)
            await doc.save()
            count += 1
            
            if count % 100 == 0:
                print(f"Migrated {count} documents...")
        
        print(f"✅ Migration complete: {count} documents")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await Database.disconnect()

if __name__ == "__main__":
    asyncio.run(migrate())
```

### 3. Large Collection Migration

For collections with millions of documents:

```python
async def migrate_in_batches(batch_size=1000):
    """Migrate large collections efficiently"""
    
    last_id = None
    total = 0
    
    while True:
        # Query in batches
        query = {} if not last_id else {"_id": {"$gt": last_id}}
        
        docs = await [Model].find(query)\
            .sort("_id")\
            .limit(batch_size)\
            .to_list()
        
        if not docs:
            break
        
        # Process batch
        for doc in docs:
            doc.new_field = calculate_value(doc)
        
        # Bulk save
        await [Model].save_all(docs)
        
        last_id = docs[-1].id
        total += len(docs)
        print(f"Processed {total} documents...")
    
    return total
```

## Testing Schema Changes

### 1. Unit Tests
```python
async def test_new_field_default():
    """Test new field has correct default"""
    video = Video(title="Test")
    await video.create()
    
    assert video.quality_score == 0.0
    assert video.tags == []

async def test_backward_compatibility():
    """Test old data still works"""
    # Insert with old schema
    old_data = {"title": "Old Video", "status": "processing"}
    await Video.get_motor_collection().insert_one(old_data)
    
    # Read with new schema
    video = await Video.find_one({"title": "Old Video"})
    assert video is not None
    assert video.quality_score == 0.0  # Default applied
```

### 2. Migration Tests
```python
async def test_migration_script():
    """Test migration handles edge cases"""
    # Create test data
    await create_test_documents()
    
    # Run migration
    result = await migrate_processing_version()
    
    # Verify results
    assert result["success"] == True
    assert result["migrated"] == 10
    
    # Check documents updated
    for video in await Video.find_all().to_list():
        assert video.processing_version is not None
```

## Rollback Plan

### 1. Schema Rollback
Keep old schema for quick rollback:
```python
# backup/models_backup_[date].py
# Copy of models before changes
```

### 2. Data Rollback
Before migration:
```bash
# Backup collection
mongodump --uri="$MONGODB_URL" \
  --collection=videos \
  --out=backup/$(date +%Y%m%d)
```

### 3. Code Rollback
```bash
# Tag release before schema change
git tag pre-schema-update-$(date +%Y%m%d)
git push origin --tags
```

## Deployment Process

### 1. Pre-Deployment
- [ ] Schema changes reviewed
- [ ] Migration script tested
- [ ] Rollback plan ready
- [ ] Team notified

### 2. Deployment Steps
1. **Deploy new code** (with backward compatible schema)
2. **Run migration script** (if needed)
3. **Verify functionality**
4. **Monitor for issues**

### 3. Post-Deployment
- [ ] Verify all services working
- [ ] Check error rates
- [ ] Validate data integrity
- [ ] Update documentation

## Common Patterns

### Adding Computed Fields
```python
class Video(Document):
    duration: float
    chunk_count: int = Field(default=0)
    
    @property
    def average_chunk_duration(self) -> float:
        """Computed property"""
        if self.chunk_count == 0:
            return 0.0
        return self.duration / self.chunk_count
```

### Soft Delete Pattern
```python
class Video(Document):
    deleted_at: Optional[datetime] = None
    
    @classmethod
    async def find_active(cls):
        """Find non-deleted documents"""
        return cls.find(cls.deleted_at == None)
    
    async def soft_delete(self):
        """Mark as deleted without removing"""
        self.deleted_at = datetime.now(timezone.utc)
        await self.save()
```

### Version Tracking
```python
class Video(Document):
    schema_version: int = Field(default=2)
    
    @validator('*', pre=True)
    def migrate_on_load(cls, v, values):
        """Migrate old schema on read"""
        version = values.get('schema_version', 1)
        if version < 2:
            # Apply migrations
            pass
        return v
```

## Documentation Updates

After schema changes:

1. **Update Model Documentation**
```python
class Video(Document):
    """
    Video document with enhanced metadata.
    
    Schema Version: 2
    Last Updated: 2024-01-15
    
    Changes:
    - Added quality_score field
    - Added tags for categorization
    - Optimized indexes for search
    """
```

2. **Update API Documentation**
- New fields in responses
- New filter parameters
- Deprecated field notices

3. **Update Knowledge Base**
```bash
./dev-cli prompt knowledge-add --type "schema-change"
```

## Checklist

- [ ] Current schema analyzed
- [ ] Changes align with PRD
- [ ] Impact assessment complete
- [ ] Backward compatibility ensured
- [ ] Migration script created
- [ ] Tests written
- [ ] Rollback plan ready
- [ ] Documentation updated
- [ ] Team notified
- [ ] Monitoring prepared

## Related Prompts
- `arch-decision` - For major architecture changes
- `impl-plan` - Implementation planning
- `test` - Testing strategies
- `doc-sync` - Documentation updates