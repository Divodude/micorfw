# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-15

### Added
- Initial release of MicroFW
- Async-first ASGI architecture
- Built-in service registry and client for microservices
- Robust middleware system with abstract base class
- SQLAlchemy async ORM integration
- Database middleware with automatic session management
- Transaction middleware for automatic commit/rollback
- Concurrency control middleware
- Pydantic integration for request/response validation
- Dependency injection for requests, database sessions, and models
- Context propagation for distributed tracing
- Lifecycle events (startup/shutdown hooks)
- Centralized configuration via environment variables
- Comprehensive documentation and examples
- Load testing results demonstrating high performance

### Features
- Route handling with path parameters
- HTTP method support (GET, POST, PUT, DELETE)
- Automatic trace ID and span propagation
- Request deadline enforcement
- Service-to-service communication with timeout handling
- Custom middleware support
- Per-route middleware configuration
- Database transaction management
- Concurrency limiting to prevent overload

[0.1.0]: https://github.com/divyanshyadav/microfw/releases/tag/v0.1.0
