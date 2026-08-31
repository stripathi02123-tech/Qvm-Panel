"""
QVM Panel - MongoDB Database Layer
Replaces SQLite with MongoDB for cloud-hosted database.
Developer: QVM Panel
"""

import os
import json
import logging
from datetime import datetime, timedelta
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError, ConnectionFailure

logger = logging.getLogger('qvm_panel')

# ─── MongoDB Configuration ───────────────────────────────
MONGODB_URI = os.getenv(
    'MONGODB_URI',
    'mongodb+srv://risalnrisal6_db_user:RnqZ8KY0cmpqAdwX@cluster0.ayj0mp0.mongodb.net/?appName=Cluster0'
)
MONGODB_DB = os.getenv('MONGODB_DB', 'qvm_panel')

# ─── Global Connection ───────────────────────────────────
_client: Optional[MongoClient] = None
_db = None


def get_client() -> MongoClient:
    """Get or create MongoDB client (singleton, lazy)"""
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=10000,
            )
            # Force connection on first use
            _client.admin.command('ping')
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    return _client


def get_database():
    """Get the database instance"""
    global _db
    if _db is None:
        _db = get_client()[MONGODB_DB]
    return _db


class Document(dict):
    """Dictionary subclass that supports attribute access (like sqlite3.Row)"""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'Document' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        self[name] = value


class Cursor:
    """Wrapper around MongoDB cursor to provide sqlite3-like interface"""

    def __init__(self, db=None, query: str = '', params=None):
        if db is not None:
            self._db = db
        else:
            self._db = get_database()
        self._result = None
        self.rowcount = 0
        self.lastrowid = None
        if query:
            self.execute(query, params)

    def execute(self, query: str, params=None):
        """Parse simple SQL-like query and execute MongoDB operation"""
        query = query.strip()
        params = params or []

        if query.upper().startswith('INSERT'):
            self._execute_insert(query, params)
        elif query.upper().startswith('SELECT'):
            self._execute_select(query, params)
        elif query.upper().startswith('UPDATE'):
            self._execute_update(query, params)
        elif query.upper().startswith('DELETE'):
            self._execute_delete(query, params)
        elif query.upper().startswith('CREATE'):
            self._execute_create(query, params)
        elif query.upper().startswith('ALTER'):
            pass  # MongoDB handles schema changes dynamically
        elif query.upper().startswith('INSERT OR IGNORE') or query.upper().startswith('INSERT OR REPLACE'):
            self._execute_upsert(query, params)
        else:
            logger.warning(f"Unsupported query: {query[:50]}...")

    def _execute_insert(self, query: str, params):
        """Handle INSERT statements"""
        try:
            # Parse table name
            table = self._parse_table_name(query)
            collection = self._db[table]

            if params:
                result = collection.insert_one(dict(params))
                self.lastrowid = result.inserted_id
                self.rowcount = 1
            self._result = None
        except DuplicateKeyError:
            logger.debug(f"Duplicate key in insert, skipping")
            self.rowcount = 0
        except Exception as e:
            logger.error(f"Insert error: {e}")

    def _execute_select(self, query: str, params):
        """Handle SELECT statements"""
        try:
            table = self._parse_table_name(query)
            collection = self._db[table]
            filter_doc = self._parse_where(query, params)

            # Parse fields
            fields = None
            if 'SELECT *' not in query.upper():
                fields = self._parse_fields(query)

            # Parse LIMIT
            limit = self._parse_limit(query)

            # Parse ORDER BY
            sort = self._parse_order_by(query)

            if fields:
                cursor = collection.find(filter_doc, fields)
            else:
                cursor = collection.find(filter_doc)

            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)

            self._result = [Document(doc) for doc in cursor]
            self.rowcount = len(self._result)
        except Exception as e:
            logger.error(f"Select error: {e}")
            self._result = []

    def _execute_update(self, query: str, params):
        """Handle UPDATE statements"""
        try:
            table = self._parse_table_name(query)
            collection = self._db[table]
            filter_doc = self._parse_where(query, params)
            update_doc = self._parse_set(query, params)

            if update_doc:
                result = collection.update_many(filter_doc, {'$set': update_doc})
                self.rowcount = result.modified_count
            self._result = None
        except Exception as e:
            logger.error(f"Update error: {e}")

    def _execute_delete(self, query: str, params):
        """Handle DELETE statements"""
        try:
            table = self._parse_table_name(query)
            collection = self._db[table]
            filter_doc = self._parse_where(query, params)

            result = collection.delete_many(filter_doc)
            self.rowcount = result.deleted_count
            self._result = None
        except Exception as e:
            logger.error(f"Delete error: {e}")

    def _execute_upsert(self, query: str, params):
        """Handle INSERT OR IGNORE / INSERT OR REPLACE"""
        try:
            table = self._parse_table_name(query)
            collection = self._db[table]
            if params:
                doc = dict(params)
                # Try to find unique key from the document
                collection.update_one(
                    {'_id': doc.get('_id', list(doc.values())[0] if doc else None)},
                    {'$set': doc},
                    upsert=True
                )
                self.rowcount = 1
            self._result = None
        except Exception as e:
            logger.error(f"Upsert error: {e}")

    def _execute_create(self, query: str, params):
        """Handle CREATE TABLE / CREATE INDEX (no-op for MongoDB)"""
        pass

    def fetchone(self):
        """Fetch next row"""
        if self._result and len(self._result) > 0:
            return self._result.pop(0)
        return None

    def fetchall(self):
        """Fetch all rows"""
        result = self._result or []
        self._result = None
        return result

    def _parse_table_name(self, query: str) -> str:
        """Extract table name from query"""
        q = query.upper()
        for keyword in ['FROM', 'INTO', 'UPDATE', 'DELETE FROM']:
            idx = q.find(keyword)
            if idx != -1:
                rest = query[idx + len(keyword):].strip()
                # Handle table name (stop at space, comma, WHERE, etc.)
                table = ''
                for char in rest:
                    if char in ' ,(':
                        break
                    table += char
                return table.lower().strip()
        return 'unknown'

    def _parse_where(self, query: str, params) -> dict:
        """Parse WHERE clause into MongoDB filter"""
        doc = {}
        q = query.upper()
        where_idx = q.find('WHERE')
        if where_idx == -1:
            return doc

        where_clause = query[where_idx + 5:].strip()

        # Remove ORDER BY, LIMIT, etc.
        for keyword in ['ORDER BY', 'LIMIT', 'GROUP BY']:
            idx = where_clause.upper().find(keyword)
            if idx != -1:
                where_clause = where_clause[:idx].strip()

        # Parse conditions
        conditions = self._split_conditions(where_clause)
        param_idx = 0

        for condition in conditions:
            condition = condition.strip()
            if not condition:
                continue

            # Handle OR
            if condition.upper().startswith('OR '):
                condition = condition[3:].strip()

            if '=' in condition and '!=' not in condition and '<>' not in condition:
                parts = condition.split('=', 1)
                key = parts[0].strip().strip('`"\'')
                val_template = parts[1].strip().strip('`"\'')

                if val_template == 'NULL':
                    doc[key] = None
                elif val_template == '?':
                    if param_idx < len(params):
                        doc[key] = params[param_idx]
                        param_idx += 1
                elif val_template.startswith("'") and val_template.endswith("'"):
                    doc[key] = val_template[1:-1]
                else:
                    try:
                        doc[key] = int(val_template)
                    except ValueError:
                        try:
                            doc[key] = float(val_template)
                        except ValueError:
                            doc[key] = val_template
            elif '!=' in condition or '<>' in condition:
                sep = '!=' if '!=' in condition else '<>'
                parts = condition.split(sep, 1)
                key = parts[0].strip().strip('`"\'')
                val_template = parts[1].strip().strip('`"\'')
                if val_template == '?':
                    if param_idx < len(params):
                        doc[key] = {'$ne': params[param_idx]}
                        param_idx += 1
                elif val_template == 'NULL':
                    doc[key] = {'$ne': None}
            elif '>' in condition:
                parts = condition.split('>', 1)
                key = parts[0].strip().strip('`"\'')
                val_template = parts[1].strip().strip('`"\'')
                if val_template == '?':
                    if param_idx < len(params):
                        doc[key] = {'$gt': params[param_idx]}
                        param_idx += 1
            elif '<' in condition:
                parts = condition.split('<', 1)
                key = parts[0].strip().strip('`"\'')
                val_template = parts[1].strip().strip('`"\'')
                if val_template == '?':
                    if param_idx < len(params):
                        doc[key] = {'$lt': params[param_idx]}
                        param_idx += 1
            elif 'LIKE' in condition.upper():
                parts = condition.upper().split('LIKE', 1)
                key = parts[0].strip().strip('`"\'')
                val_template = parts[1].strip().strip('`"\'')
                if val_template == '?':
                    if param_idx < len(params):
                        import re as regex_mod
                        pattern = params[param_idx].replace('%', '.*')
                        doc[key] = {'$regex': pattern, '$options': 'i'}
                        param_idx += 1

        return doc

    def _split_conditions(self, where_clause: str) -> list:
        """Split WHERE clause by AND"""
        conditions = []
        current = ''
        i = 0
        q = where_clause.upper()
        while i < len(where_clause):
            if q[i:i+4] == ' AND' and (i+4 >= len(q) or q[i+4] in ' ('):
                conditions.append(current.strip())
                current = ''
                i += 4
            else:
                current += where_clause[i]
                i += 1
        if current.strip():
            conditions.append(current.strip())
        return conditions

    def _parse_set(self, query: str, params) -> dict:
        """Parse SET clause into MongoDB update document"""
        doc = {}
        q = query.upper()
        set_idx = q.find('SET')
        if set_idx == -1:
            return doc

        set_clause = query[set_idx + 3:].strip()

        # Remove WHERE clause
        where_idx = set_clause.upper().find('WHERE')
        if where_idx != -1:
            set_clause = set_clause[:where_idx].strip()

        # Parse assignments
        parts = set_clause.split(',')
        param_idx = 0

        for part in parts:
            part = part.strip()
            if '=' in part:
                key, val_template = part.split('=', 1)
                key = key.strip().strip('`"\'')
                val_template = val_template.strip().strip('`"\'')

                if val_template == '?':
                    if param_idx < len(params):
                        doc[key] = params[param_idx]
                        param_idx += 1
                elif val_template == 'NULL':
                    doc[key] = None
                elif val_template == 'CURRENT_TIMESTAMP':
                    doc[key] = datetime.now().isoformat()
                elif val_template.startswith("'") and val_template.endswith("'"):
                    doc[key] = val_template[1:-1]
                else:
                    try:
                        doc[key] = int(val_template)
                    except ValueError:
                        doc[key] = val_template

        return doc

    def _parse_fields(self, query: str) -> dict:
        """Parse SELECT fields into MongoDB projection"""
        q = query.upper()
        select_idx = q.find('SELECT')
        from_idx = q.find('FROM')
        if select_idx == -1 or from_idx == -1:
            return None

        fields_str = query[select_idx + 6:from_idx].strip()
        if fields_str == '*':
            return None

        fields = {}
        for field in fields_str.split(','):
            field = field.strip().strip('`"\'')
            if field:
                fields[field] = 1
        return fields

    def _parse_limit(self, query: str) -> Optional[int]:
        """Parse LIMIT clause"""
        q = query.upper()
        idx = q.find('LIMIT')
        if idx == -1:
            return None
        rest = query[idx + 6:].strip()
        try:
            return int(rest.split()[0])
        except (ValueError, IndexError):
            return None

    def _parse_order_by(self, query: str):
        """Parse ORDER BY clause"""
        q = query.upper()
        idx = q.find('ORDER BY')
        if idx == -1:
            return None
        rest = query[idx + 8:].strip()
        parts = rest.split()
        if len(parts) >= 2:
            field = parts[0].strip('`"\'')
            direction = DESCENDING if parts[1].upper() == 'DESC' else ASCENDING
            return [(field, direction)]
        elif len(parts) == 1:
            return [(parts[0].strip('`"\''), ASCENDING)]
        return None


# ─── Database Helper Functions ───────────────────────────

def init_db():
    """Initialize MongoDB collections and indexes"""
    db = get_database()

    # Create indexes for common queries
    try:
        db.users.create_index('username', unique=True)
        db.users.create_index('email', unique=True)
        db.users.create_index('api_key', sparse=True)
        db.users.create_index('discord_id', sparse=True)
        db.users.create_index('google_id', sparse=True)
        db.vps.create_index('user_id')
        db.vps.create_index('node_id')
        db.vps.create_index('container_name', unique=True)
        db.vps.create_index('status')
        db.vps.create_index('suspended')
        db.vps.create_index('expires_at', sparse=True)
        db.nodes.create_index('name', unique=True)
        db.nodes.create_index('api_key', sparse=True)
        db.port_forwards.create_index('user_id')
        db.port_forwards.create_index('vps_container')
        db.port_forwards.create_index('host_port')
        db.notifications.create_index('user_id')
        db.notifications.create_index([('user_id', ASCENDING), ('read', ASCENDING)])
        db.activity_logs.create_index('user_id')
        db.activity_logs.create_index('created_at')
        db.backups.create_index('vps_id')
        db.ai_conversations.create_index('user_id')
        db.protection_events.create_index('vps_id')
        db.settings.create_index('key', unique=True)
        db.themes.create_index('is_active')
        db.api_keys.create_index('key', unique=True)
        db.api_keys.create_index('user_id')
        logger.info("MongoDB indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

    # Create default admin user if not exists
    from werkzeug.security import generate_password_hash
    import secrets

    admin_username = os.getenv('MAIN_ADMIN_USERNAME', 'admin')
    admin_email = os.getenv('MAIN_ADMIN_EMAIL', 'admin@localhost')
    admin_password = os.getenv('MAIN_ADMIN_PASSWORD', 'admin')

    existing = db.users.find_one({'is_main_admin': 1})
    if not existing:
        now = datetime.now().isoformat()
        api_key = secrets.token_urlsafe(64)
        db.users.insert_one({
            'username': admin_username,
            'email': admin_email,
            'password_hash': generate_password_hash(admin_password),
            'is_admin': 1,
            'is_main_admin': 1,
            'created_at': now,
            'last_login': now,
            'last_active': now,
            'api_key': api_key,
            'profile_picture': None,
            'preferences': '{}',
            'two_factor_secret': None,
            'two_factor_enabled': 0,
            'theme': 'default',
            'language': 'en',
            'discord_id': None,
            'discord_username': None,
            'discord_avatar': None,
            'discord_email': None,
            'google_id': None,
            'google_username': None,
            'google_email': None,
            'google_avatar': None,
        })
        # Create port allocation for admin
        admin_user = db.users.find_one({'is_main_admin': 1})
        if admin_user:
            db.port_allocations.insert_one({
                'user_id': admin_user['_id'],
                'allocated_ports': 100,
                'used_ports': 0,
                'updated_at': now,
            })
        logger.info("Default admin user created")

    # Initialize settings
    settings_init = [
        ('cpu_threshold', '90', 'CPU usage threshold for auto-suspension (%)'),
        ('ram_threshold', '90', 'RAM usage threshold for auto-suspension (%)'),
        ('site_name', 'QVM Panel', 'Site name'),
        ('site_description', 'High-Performance VPS Management Panel', 'Site description'),
        ('header_icon', '/static/img/logo.svg', 'Header icon path'),
        ('favicon', '/static/img/favicon.ico', 'Favicon path'),
        ('footer_text', 'Powered by QVM Panel © QVM Panel 2026 | Version 1.0', 'Footer text'),
        ('maintenance_mode', '0', 'Maintenance mode (1=enabled, 0=disabled)'),
        ('maintenance_message', 'Site is under maintenance. Please check back later.', 'Maintenance message'),
        ('registration_enabled', '1', 'Registration enabled (1=enabled, 0=disabled)'),
        ('default_port_quota', '5', 'Default port quota for new users'),
        ('max_vps_per_user', '10', 'Maximum VPS per user'),
        ('session_timeout', '86400', 'Session timeout in seconds'),
        ('backup_enabled', '1', 'Auto backup enabled'),
        ('backup_retention', '7', 'Number of backups to retain'),
        ('smtp_host', '', 'SMTP host'),
        ('smtp_port', '587', 'SMTP port'),
        ('smtp_user', '', 'SMTP username'),
        ('smtp_pass', '', 'SMTP password'),
        ('smtp_from', '', 'SMTP from email'),
        ('theme', 'default', 'Default theme'),
        ('language', 'en', 'Default language'),
        ('timezone', 'Asia/Kolkata', 'Default timezone'),
        ('discord_auth_enabled', '0', 'Discord auth enabled'),
        ('discord_client_id', '', 'Discord client ID'),
        ('discord_client_secret', '', 'Discord client secret'),
        ('discord_redirect_uri', 'http://localhost:5000/auth/discord/callback', 'Discord redirect URI'),
        ('discord_auto_register', '1', 'Discord auto register'),
        ('discord_button_text', 'Continue with Discord', 'Discord button text'),
        ('google_auth_enabled', '0', 'Google auth enabled'),
        ('google_client_id', '', 'Google client ID'),
        ('google_client_secret', '', 'Google client secret'),
        ('google_redirect_uri', 'http://localhost:5000/auth/google/callback', 'Google redirect URI'),
        ('google_auto_register', '1', 'Google auto register'),
        ('google_button_text', 'Continue with Google', 'Google button text'),
        ('discord_bot_enabled', '0', 'Discord bot enabled'),
        ('discord_bot_token', '', 'Discord bot token'),
        ('discord_bot_guild_id', '', 'Discord bot guild ID'),
        ('discord_bot_admin_channel', '', 'Discord bot admin channel'),
        ('discord_bot_log_channel', '', 'Discord bot log channel'),
        ('discord_bot_command_prefix', '!', 'Discord bot command prefix'),
        ('discord_bot_deploy_role', '', 'Discord bot deploy role'),
        ('vm_enabled', '0', 'VM enabled'),
        ('vm_storage_pool', '/var/lib/libvirt/images', 'VM storage pool'),
        ('vm_default_ram', '2048', 'VM default RAM'),
        ('vm_default_cpu', '2', 'VM default CPU'),
        ('vm_default_disk', '20', 'VM default disk'),
        ('vm_cloudinit_images', json.dumps([
            {'name': 'Debian 12', 'url': 'https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-amd64.qcow2', 'os': 'debian'},
            {'name': 'Ubuntu 24.04', 'url': 'https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img', 'os': 'ubuntu'}
        ]), 'VM cloud-init images'),
        ('vm_novnc_port', '6080', 'VM noVNC port'),
        ('vm_novnc_enabled', '1', 'VM noVNC enabled'),
    ]

    for key, value, description in settings_init:
        existing = db.settings.find_one({'key': key})
        if not existing:
            db.settings.insert_one({
                'key': key,
                'value': value,
                'description': description,
                'updated_at': datetime.now().isoformat(),
            })

    # Initialize default theme
    existing_theme = db.themes.find_one({'name': 'Default'})
    if not existing_theme:
        now = datetime.now().isoformat()
        db.themes.insert_one({
            'name': 'Default',
            'description': 'Default QVM dark theme',
            'bg_primary': '#0a0c10',
            'bg_secondary': '#111316',
            'accent_primary': '#3b82f6',
            'accent_secondary': '#6366f1',
            'text_primary': '#e1e9f0',
            'gif_url': '',
            'gif_file': None,
            'is_active': 1,
            'created_by': None,
            'created_at': now,
            'updated_at': now,
        })

    # Create default port allocations for users without one
    all_users = list(db.users.find({}, {'_id': 1}))
    for user in all_users:
        existing_alloc = db.port_allocations.find_one({'user_id': user['_id']})
        if not existing_alloc:
            db.port_allocations.insert_one({
                'user_id': user['_id'],
                'allocated_ports': 5,
                'used_ports': 0,
                'updated_at': datetime.now().isoformat(),
            })

    logger.info("MongoDB initialization complete")


@contextmanager
def get_db():
    """Context manager that provides a MongoDB-compatible interface"""
    client = get_client()
    try:
        yield client[MONGODB_DB]
    except ConnectionFailure as e:
        logger.error(f"MongoDB connection error: {e}")
        raise


def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting from the database"""
    try:
        db = get_database()
        row = db.settings.find_one({'key': key})
        return row['value'] if row else default
    except Exception:
        return default


def set_setting(key: str, value: str):
    """Set a setting in the database"""
    try:
        db = get_database()
        db.settings.update_one(
            {'key': key},
            {'$set': {'value': value, 'updated_at': datetime.now().isoformat()}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")


def log_activity(user_id, action, resource_type=None, resource_id=None, details=None):
    """Log activity to database"""
    try:
        from flask import request as flask_request
        db = get_database()
        db.activity_logs.insert_one({
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': json.dumps(details) if details else None,
            'ip_address': flask_request.remote_addr if flask_request else None,
            'user_agent': flask_request.user_agent.string if flask_request and hasattr(flask_request, 'user_agent') else None,
            'created_at': datetime.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Failed to log activity: {e}")


def create_notification(user_id: int, ntype: str, title: str, message: str, data=None, expires_in=None):
    """Create a notification"""
    try:
        db = get_database()
        expires_at = None
        if expires_in:
            expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        result = db.notifications.insert_one({
            'user_id': user_id,
            'type': ntype,
            'title': title,
            'message': message,
            'read': 0,
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at,
            'data': json.dumps(data) if data else None,
        })

        # Emit via SocketIO if available
        try:
            from avm import socketio
            if socketio:
                socketio.emit('new_notification', {
                    'id': str(result.inserted_id),
                    'type': ntype,
                    'title': title,
                    'message': message,
                    'created_at': datetime.now().isoformat()
                }, room=f'user_{user_id}')
        except:
            pass
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")


def get_user_notifications(user_id: int, unread_only=False, limit=50):
    """Get notifications for a user"""
    try:
        db = get_database()
        query = {'user_id': user_id}
        if unread_only:
            query['read'] = 0
        query['$or'] = [
            {'expires_at': None},
            {'expires_at': {'$gt': datetime.now().isoformat()}}
        ]

        notifications = list(db.notifications.find(query).sort('created_at', DESCENDING).limit(limit))

        for notif in notifications:
            notif['_id'] = str(notif['_id'])
            if notif.get('data'):
                try:
                    notif['data'] = json.loads(notif['data'])
                except:
                    notif['data'] = {}

        return notifications
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return []


def mark_notification_read(notification_id, user_id):
    """Mark a notification as read"""
    try:
        from bson import ObjectId
        db = get_database()
        result = db.notifications.update_one(
            {'_id': ObjectId(notification_id), 'user_id': user_id},
            {'$set': {'read': 1}}
        )
        return result.modified_count > 0
    except:
        return False


def mark_all_notifications_read(user_id):
    """Mark all notifications as read"""
    try:
        db = get_database()
        result = db.notifications.update_many(
            {'user_id': user_id, 'read': 0},
            {'$set': {'read': 1}}
        )
        return result.modified_count
    except:
        return 0


def get_unread_notifications_count(user_id: int) -> int:
    """Get count of unread notifications"""
    try:
        db = get_database()
        return db.notifications.count_documents({
            'user_id': user_id,
            'read': 0,
            '$or': [
                {'expires_at': None},
                {'expires_at': {'$gt': datetime.now().isoformat()}}
            ]
        })
    except:
        return 0


def generate_api_key(length=64):
    """Generate a random API key"""
    import secrets
    return secrets.token_urlsafe(length)
