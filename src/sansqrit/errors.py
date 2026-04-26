"""Sansqrit exception hierarchy."""

class SansqritError(Exception):
    """Base exception for Sansqrit."""

class SansqritSyntaxError(SansqritError):
    """Raised when Sansqrit source cannot be translated."""

class SansqritRuntimeError(SansqritError):
    """Raised for DSL/runtime errors."""

class QuantumError(SansqritError):
    """Raised for invalid quantum operations."""
