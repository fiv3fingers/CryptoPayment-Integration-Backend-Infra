# models/schemas/base.py
from pydantic import BaseModel
from datetime import datetime

class TimestampModel(BaseModel):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 


class MetadataModel(BaseModel):
    @classmethod
    def from_orm(cls, obj):
        data = {
            key: getattr(obj, key) 
            for key in cls.model_fields.keys()
        }
        # Special handling for metadata
        data['metadata'] = obj.metadata_
        return cls(**data)

    def to_orm_dict(self, **kwargs):    # kwargs go to model_dump
        data = self.model_dump(**kwargs)
        # Convert metadata back to metadata_
        if 'metadata' in data:
            data['metadata_'] = data.pop('metadata')
        return data

