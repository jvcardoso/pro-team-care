from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY, HTTP_500_INTERNAL_SERVER_ERROR
import structlog

logger = structlog.get_logger()


class BusinessException(Exception):
    """Exceção para regras de negócio"""
    def __init__(self, message: str, code: str = "BUSINESS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationException(Exception):
    """Exceção para erros de validação"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class NotFoundException(Exception):
    """Exceção para recursos não encontrados"""
    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """Handler para exceções de negócio"""
    logger.warning(
        "Business exception occurred",
        path=request.url.path,
        method=request.method,
        code=exc.code,
        message=exc.message
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "type": "business_error"
            }
        }
    )


async def validation_exception_handler(request: Request, exc: ValidationException) -> JSONResponse:
    """Handler para exceções de validação"""
    logger.warning(
        "Validation exception occurred",
        path=request.url.path,
        method=request.method,
        field=exc.field,
        message=exc.message
    )
    
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "field": exc.field,
                "type": "validation_error"
            }
        }
    )


async def not_found_exception_handler(request: Request, exc: NotFoundException) -> JSONResponse:
    """Handler para exceções de recurso não encontrado"""
    logger.warning(
        "Resource not found",
        path=request.url.path,
        method=request.method,
        message=exc.message
    )
    
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "NOT_FOUND",
                "message": exc.message,
                "type": "not_found_error"
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler para exceções gerais"""
    logger.error(
        "Unexpected error occurred",
        path=request.url.path,
        method=request.method,
        exception=str(exc),
        exception_type=type(exc).__name__
    )
    
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
                "type": "internal_error"
            }
        }
    )