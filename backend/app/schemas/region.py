from pydantic import BaseModel

class RegionOut(BaseModel):
    code: str
    name: str

    class Config:
        from_attributes = True