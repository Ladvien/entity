"""Pydantic configuration models for infrastructure components."""

from pydantic import BaseModel, Field, validator
from typing import Optional


class DuckDBConfig(BaseModel):
    """Configuration for DuckDB infrastructure."""
    
    file_path: str = Field(default=":memory:", description="Path to DuckDB file or ':memory:'")
    pool_size: int = Field(default=5, ge=1, le=100, description="Connection pool size")
    version: Optional[str] = None
    
    @validator('file_path')
    def validate_file_path(cls, v):
        if v != ":memory:" and not v:
            raise ValueError("file_path must be ':memory:' or a valid path")
        return v


class VLLMConfig(BaseModel):
    """Configuration for vLLM infrastructure."""
    
    base_url: Optional[str] = None
    model: Optional[str] = None
    auto_detect_model: bool = Field(default=True, description="Auto-detect optimal model based on hardware")
    gpu_memory_utilization: float = Field(default=0.9, ge=0.1, le=1.0)
    port: Optional[int] = Field(default=None, ge=1024, le=65535)
    version: Optional[str] = None
    
    @validator('gpu_memory_utilization')
    def validate_gpu_memory(cls, v):
        if not 0.1 <= v <= 1.0:
            raise ValueError("gpu_memory_utilization must be between 0.1 and 1.0")
        return v


class OllamaConfig(BaseModel):
    """Configuration for Ollama infrastructure."""
    
    base_url: str = Field(..., description="Ollama server URL")
    model: str = Field(..., description="Model name to use")
    version: Optional[str] = None
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        return v.rstrip('/')


class LocalStorageConfig(BaseModel):
    """Configuration for local storage infrastructure."""
    
    base_path: str = Field(..., description="Base directory for storage")
    permissions: int = Field(default=0o755, description="Directory permissions")
    version: Optional[str] = None
    
    @validator('permissions')
    def validate_permissions(cls, v):
        if not 0 <= v <= 0o777:
            raise ValueError("permissions must be a valid octal mode")
        return v


class S3Config(BaseModel):
    """Configuration for S3 infrastructure."""
    
    bucket: str = Field(..., description="S3 bucket name")
    region: Optional[str] = Field(default=None, description="AWS region")
    endpoint_url: Optional[str] = Field(default=None, description="Custom endpoint URL")
    version: Optional[str] = None
    
    @validator('bucket')
    def validate_bucket_name(cls, v):
        if not v or len(v) < 3 or len(v) > 63:
            raise ValueError("bucket name must be between 3 and 63 characters")
        return v