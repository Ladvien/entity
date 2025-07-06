# Unified Registry Prototype

This directory contains a prototype `AsyncResourceManager` designed for small
experiments with dependency injection frameworks like FastAPI and Django.

Key features:

- Asynchronous resource registration and initialization
- Health checks for all managed resources
- Simple metrics collection
- Example FastAPI integration in `di_demo.py`

The same manager can be integrated with Django by creating the instance inside
`apps.py` and exposing resources through dependency injection utilities.
