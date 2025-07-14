# PostgreSQL Performance Monitor

## Overview

This is a real-time PostgreSQL database performance monitoring dashboard built with Streamlit. The application provides live monitoring capabilities for PostgreSQL databases, displaying key performance metrics and connection statistics through an interactive web interface.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit - chosen for rapid development of data-driven web applications
- **Visualization**: Plotly (graph_objects and express) for interactive charts and graphs
- **Data Processing**: Pandas for data manipulation and analysis
- **UI Components**: Streamlit's built-in components for controls, metrics, and layout

### Backend Architecture
- **Database Driver**: psycopg2 for PostgreSQL connectivity
- **Connection Management**: Custom DatabaseMonitor class handles connection pooling and query execution
- **Error Handling**: Comprehensive exception handling for database operations
- **Caching**: Streamlit's caching system for performance optimization

### Data Storage Solutions
- **Primary Database**: PostgreSQL (currently configured for Neon cloud service)
- **Connection String**: Environment variable support with fallback to hardcoded connection
- **SSL Mode**: Required SSL connections for security

## Key Components

### DatabaseMonitor Class (`database.py`)
- Handles all database connections and queries
- Provides connection testing with ping measurement
- Manages database information retrieval
- Uses cursor factory for dictionary-style result sets

### Utility Functions (`utils.py`)
- `format_bytes()`: Converts byte values to human-readable format
- `format_duration()`: Formats time durations for display
- `get_status_color()`: Maps status strings to color indicators

### Main Application (`app.py`)
- Streamlit web application entry point
- Real-time dashboard with auto-refresh functionality
- Sidebar controls for refresh settings
- Wide layout configuration for optimal data display

## Data Flow

1. **Connection Initialization**: Database connection established using environment variable or fallback URL
2. **Health Check**: Connection testing with ping measurement
3. **Data Retrieval**: Database metrics queried through DatabaseMonitor
4. **Data Processing**: Raw data formatted using utility functions
5. **Visualization**: Processed data displayed through Plotly charts
6. **Real-time Updates**: Auto-refresh mechanism updates dashboard at configurable intervals

## External Dependencies

### Core Libraries
- `streamlit`: Web application framework
- `psycopg2`: PostgreSQL database adapter
- `plotly`: Interactive visualization library
- `pandas`: Data manipulation and analysis

### Database Service
- **Neon**: Cloud PostgreSQL service (current configuration)
- **Connection**: SSL-required connection to AWS US-East-2 region
- **Fallback**: Environment variable support for flexible deployment

## Deployment Strategy

### Environment Configuration
- Database URL configured through `DATABASE_URL` environment variable
- Fallback connection string provided for development/testing
- SSL mode enforced for production security

### Streamlit Configuration
- Page configured with PostgreSQL elephant icon
- Wide layout for dashboard optimization
- Expanded sidebar for better control access

### Caching Strategy
- Streamlit resource caching for database monitor instance
- Manual cache clearing for refresh functionality
- Performance optimization through connection reuse

### Error Handling
- Comprehensive exception handling for database operations
- User-friendly error messages
- Graceful degradation when database unavailable

## Recent Changes

### July 13, 2025
- Added export functionality for dashboard reports in 9:16 aspect ratio
- Implemented comprehensive dashboard image generation with all key metrics
- Added preview and download buttons in sidebar for report generation
- Replaced Kaleido with matplotlib for image export (Chrome dependency removed)
- Fixed index usage query compatibility issues
- Improved dashboard layout with better spacing and card-based design
- Added real-time refresh capability with millisecond-level intervals (25-500ms)

## Development Notes

The application is structured for easy extension with additional monitoring features. The modular design allows for:
- Additional database metrics through DatabaseMonitor extension
- New visualization types through Plotly integration
- Enhanced utility functions for data formatting
- Flexible database provider switching through environment variables

The current implementation focuses on core monitoring functionality with room for expansion into advanced PostgreSQL-specific metrics like query performance, index usage, and connection pool statistics.