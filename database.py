import psycopg2
import psycopg2.extras
import time
import os
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

class DatabaseMonitor:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.parsed_url = urlparse(connection_string)
        
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(self.connection_string)
            return conn
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    def test_connection(self) -> Dict[str, Any]:
        """Test database connection and measure ping"""
        result = {
            'connected': False,
            'ping_ms': None,
            'database_name': None,
            'error': None
        }
        
        try:
            start_time = time.time()
            conn = self.get_connection()
            end_time = time.time()
            
            result['connected'] = True
            result['ping_ms'] = (end_time - start_time) * 1000
            result['database_name'] = self.parsed_url.path.lstrip('/')
            
            conn.close()
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def get_database_info(self) -> Optional[Dict[str, Any]]:
        """Get basic database information"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get version
            cur.execute("SELECT version();")
            version = cur.fetchone()['version']
            
            # Get server start time
            cur.execute("SELECT pg_postmaster_start_time();")
            server_start_time = cur.fetchone()['pg_postmaster_start_time']
            
            # Get current time
            cur.execute("SELECT now();")
            current_time = cur.fetchone()['now']
            
            # Get timezone
            cur.execute("SELECT current_setting('timezone');")
            timezone = cur.fetchone()['current_setting']
            
            # Get database size
            cur.execute("SELECT pg_database_size(current_database());")
            database_size = cur.fetchone()['pg_database_size']
            
            # Get connection info
            cur.execute("SELECT count(*) as active_connections FROM pg_stat_activity;")
            active_connections = cur.fetchone()['active_connections']
            
            cur.execute("SELECT setting::int as max_connections FROM pg_settings WHERE name = 'max_connections';")
            max_connections = cur.fetchone()['max_connections']
            
            # Calculate uptime
            cur.execute("SELECT extract(epoch from (now() - pg_postmaster_start_time())) as uptime_seconds;")
            uptime_seconds = cur.fetchone()['uptime_seconds']
            
            conn.close()
            
            return {
                'version': version,
                'server_start_time': server_start_time,
                'current_time': current_time,
                'timezone': timezone,
                'database_size': database_size,
                'active_connections': active_connections,
                'max_connections': max_connections,
                'uptime_seconds': uptime_seconds
            }
            
        except Exception as e:
            print(f"Error getting database info: {e}")
            return None
    
    def get_performance_metrics(self) -> Optional[Dict[str, Any]]:
        """Get performance metrics"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            # Get cache hit ratio
            cur.execute("""
                SELECT 
                    round(
                        (sum(blks_hit) * 100.0 / sum(blks_hit + blks_read)), 2
                    ) as cache_hit_ratio
                FROM pg_stat_database 
                WHERE datname = current_database();
            """)
            cache_hit_ratio = cur.fetchone()['cache_hit_ratio'] or 0
            
            # Get transaction statistics
            cur.execute("""
                SELECT 
                    xact_commit,
                    xact_rollback,
                    blks_read,
                    blks_hit,
                    tup_returned,
                    tup_fetched,
                    tup_inserted,
                    tup_updated,
                    tup_deleted,
                    temp_files,
                    temp_bytes,
                    deadlocks
                FROM pg_stat_database 
                WHERE datname = current_database();
            """)
            stats = cur.fetchone()
            
            # Get locks
            cur.execute("SELECT count(*) as locks FROM pg_locks;")
            locks = cur.fetchone()['locks']
            
            # Calculate rates (simplified - would need time-based calculation for real rates)
            commits_per_sec = stats['xact_commit'] / max(1, stats['xact_commit'] + stats['xact_rollback'])
            rollbacks_per_sec = stats['xact_rollback'] / max(1, stats['xact_commit'] + stats['xact_rollback'])
            blocks_read_per_sec = stats['blks_read'] / max(1, stats['blks_read'] + stats['blks_hit'])
            
            conn.close()
            
            return {
                'cache_hit_ratio': cache_hit_ratio,
                'commits_per_sec': commits_per_sec,
                'rollbacks_per_sec': rollbacks_per_sec,
                'blocks_read_per_sec': blocks_read_per_sec,
                'locks': locks,
                'deadlocks': stats['deadlocks'],
                'temp_files': stats['temp_files'],
                'temp_bytes': stats['temp_bytes']
            }
            
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return None
    
    def get_query_performance(self) -> Optional[Dict[str, Any]]:
        """Test query execution times"""
        test_queries = {
            'Simple SELECT': 'SELECT 1;',
            'Current Time': 'SELECT now();',
            'Database Size': 'SELECT pg_database_size(current_database());',
            'Active Connections': 'SELECT count(*) FROM pg_stat_activity;',
            'Table Count': 'SELECT count(*) FROM information_schema.tables WHERE table_schema = \'public\';'
        }
        
        results = {}
        
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            for query_name, query in test_queries.items():
                try:
                    start_time = time.time()
                    cur.execute(query)
                    cur.fetchall()
                    end_time = time.time()
                    
                    results[query_name] = {
                        'success': True,
                        'execution_time': end_time - start_time,
                        'error': None
                    }
                except Exception as e:
                    results[query_name] = {
                        'success': False,
                        'execution_time': None,
                        'error': str(e)
                    }
            
            conn.close()
            
        except Exception as e:
            print(f"Error testing query performance: {e}")
            return None
        
        return results
    
    def get_active_connections(self) -> Optional[List[Dict[str, Any]]]:
        """Get active database connections"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("""
                SELECT 
                    pid,
                    usename,
                    application_name,
                    client_addr,
                    client_port,
                    backend_start,
                    query_start,
                    state_change,
                    state,
                    query
                FROM pg_stat_activity
                WHERE state IS NOT NULL
                ORDER BY backend_start DESC;
            """)
            
            connections = cur.fetchall()
            conn.close()
            
            return [dict(row) for row in connections]
            
        except Exception as e:
            print(f"Error getting active connections: {e}")
            return None
    
    def get_table_sizes(self) -> Optional[List[Dict[str, Any]]]:
        """Get table sizes"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("""
                SELECT 
                    schemaname,
                    tablename as table_name,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                LIMIT 20;
            """)
            
            tables = cur.fetchall()
            conn.close()
            
            return [dict(row) for row in tables]
            
        except Exception as e:
            print(f"Error getting table sizes: {e}")
            return None
    
    def get_index_usage(self) -> Optional[List[Dict[str, Any]]]:
        """Get index usage statistics"""
        try:
            conn = self.get_connection()
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            
            cur.execute("""
                SELECT 
                    schemaname,
                    relname as table_name,
                    indexrelname as index_name,
                    idx_scan as index_scans,
                    idx_tup_read as tuples_read,
                    idx_tup_fetch as tuples_fetched,
                    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
                FROM pg_stat_user_indexes
                ORDER BY idx_scan DESC
                LIMIT 20;
            """)
            
            indexes = cur.fetchall()
            conn.close()
            
            return [dict(row) for row in indexes]
            
        except Exception as e:
            print(f"Error getting index usage: {e}")
            return None
