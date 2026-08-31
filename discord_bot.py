#!/usr/bin/env python3
"""
QVM Panel - Discord Bot
Version: 1.0
Developer: QVM Panel
Description: Discord bot for managing VPS from Discord with rich embeds
"""

import os
import sys
import json
import asyncio
import sqlite3
import logging
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("ERROR: discord.py not installed. Run: pip install discord.py")

# ─── Logging ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('discord_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('avm_discord_bot')

# ─── Database ─────────────────────────────────────────────
DATABASE_PATH = os.getenv('DATABASE_PATH', 'avm.db')
PANEL_URL = os.getenv('PANEL_URL', 'http://localhost:5000')


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE_PATH, timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.row_factory = sqlite3.Row
    return conn


def get_setting(key, default=None):
    """Get a setting from the database"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cur.fetchone()
            return row[0] if row else default
    except Exception:
        return default


def get_all_vps():
    """Get all VPS from database"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT v.*, u.username, n.name as node_name 
                          FROM vps v 
                          LEFT JOIN users u ON v.user_id = u.id 
                          LEFT JOIN nodes n ON v.node_id = n.id 
                          ORDER BY v.id''')
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting VPS: {e}")
        return []


def get_vps_by_id(vps_id):
    """Get VPS by ID"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''SELECT v.*, u.username, n.name as node_name 
                          FROM vps v 
                          LEFT JOIN users u ON v.user_id = u.id 
                          LEFT JOIN nodes n ON v.node_id = n.id 
                          WHERE v.id = ?''', (vps_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting VPS {vps_id}: {e}")
        return None


def get_all_users():
    """Get all users"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('SELECT id, username, email, is_admin, is_main_admin, created_at, last_login FROM users ORDER BY id')
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []


def get_all_nodes():
    """Get all nodes"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM nodes ORDER BY id')
            return [dict(row) for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        return []


def log_activity(user_id, action, details=None):
    """Log activity to database"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''INSERT INTO activity_logs (user_id, action, resource_type, details, created_at) 
                          VALUES (?, ?, 'discord_bot', ?, ?)''',
                       (user_id, action, json.dumps(details) if details else None, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")


def create_notification(user_id, ntype, title, message):
    """Create a notification"""
    try:
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute('''INSERT INTO notifications (user_id, type, title, message, created_at) 
                          VALUES (?, ?, ?, ?, ?)''',
                       (user_id, ntype, title, message, datetime.now().isoformat()))
            conn.commit()
    except Exception as e:
        logger.error(f"Error creating notification: {e}")


# ─── Colors ───────────────────────────────────────────────
COLOR_SUCCESS = 0x10B981
COLOR_ERROR = 0xEF4444
COLOR_WARNING = 0xF59E0B
COLOR_INFO = 0x3B82F6
COLOR_PRIMARY = 0x8B5CF6
COLOR_DISCORD = 0x5865F2


# ─── Bot Setup ────────────────────────────────────────────
def create_bot():
    """Create and configure the Discord bot"""
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    
    bot = commands.Bot(
        command_prefix=get_setting('discord_bot_command_prefix', '!'),
        intents=intents,
        help_command=None
    )
    
    # ─── Events ───────────────────────────────────────────
    @bot.event
    async def on_ready():
        logger.info(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
        logger.info(f'Connected to {len(bot.guilds)} guild(s)')
        
        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f'Synced {len(synced)} slash command(s)')
        except Exception as e:
            logger.error(f'Failed to sync commands: {e}')
        
        # Set activity
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"QVM Panel | {len(bot.guilds)} server(s)"
            )
        )
    
    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="⚠️ Missing Argument",
                description=f"Missing required argument: `{error.param.name}`\nUse `{bot.command_prefix}help {ctx.command}` for usage info.",
                color=COLOR_WARNING
            )
            await ctx.send(embed=embed)
            return
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="🔒 Permission Denied",
                description="You don't have permission to use this command.",
                color=COLOR_ERROR
            )
            await ctx.send(embed=embed)
            return
        
        logger.error(f"Command error: {error}", exc_info=True)
        embed = discord.Embed(
            title="❌ Error",
            description=f"An error occurred: {str(error)[:200]}",
            color=COLOR_ERROR
        )
        await ctx.send(embed=embed)
    
    # ─── Permission Check ─────────────────────────────────
    def is_admin_or_role():
        """Check if user is admin or has the deploy role"""
        async def predicate(ctx):
            if ctx.author.guild_permissions.administrator:
                return True
            role_id = get_setting('discord_bot_deploy_role', '')
            if role_id:
                role = ctx.guild.get_role(int(role_id))
                if role and role in ctx.author.roles:
                    return True
            return False
        return commands.check(predicate)
    
    # ─── Helper: Run sync function ────────────────────────
    def run_in_thread(func, *args, **kwargs):
        """Run a synchronous function in a thread pool"""
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(func, *args, **kwargs)
    
    # ─── Commands ─────────────────────────────────────────
    
    @bot.command(name='help')
    async def help_command(ctx):
        """Show all bot commands"""
        prefix = bot.command_prefix
        
        embed = discord.Embed(
            title="🤖 QVM Panel Bot Commands",
            description="All available commands for managing your VPS panel from Discord.",
            color=COLOR_PRIMARY
        )
        
        commands_list = [
            ("📊 Status & Info", [
                f"`{prefix}status` — View all VPS status overview",
                f"`{prefix}vps <id>` — View detailed VPS info",
                f"`{prefix}nodes` — View all node status",
                f"`{prefix}users` — List all users",
                f"`{prefix}stats` — Panel statistics",
            ]),
            ("🚀 VPS Management", [
                f"`{prefix}deploy` — Interactive VPS deployment wizard",
                f"`{prefix}start <vps_id>` — Start a VPS",
                f"`{prefix}stop <vps_id>` — Stop a VPS",
                f"`{prefix}restart <vps_id>` — Restart a VPS",
                f"`{prefix}delete <vps_id>` — Delete a VPS (with confirmation)",
            ]),
            ("⚙️ Admin", [
                f"`{prefix}panel` — Get panel URL",
                f"`{prefix}ping` — Bot latency check",
            ]),
        ]
        
        for category, cmds in commands_list:
            embed.add_field(
                name=category,
                value="\n".join(cmds),
                inline=False
            )
        
        embed.set_footer(text="QVM Panel Bot v1.0 | Use / for slash commands")
        await ctx.send(embed=embed)
    
    @bot.command(name='ping')
    async def ping(ctx):
        """Check bot latency"""
        latency = round(bot.latency * 1000)
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=COLOR_SUCCESS if latency < 200 else COLOR_WARNING if latency < 500 else COLOR_ERROR
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='panel')
    @is_admin_or_role()
    async def panel_url(ctx):
        """Get panel URL"""
        embed = discord.Embed(
            title="🌐 QVM Panel",
            description=f"**Panel URL:** {PANEL_URL}\n**Status:** Online ✅",
            color=COLOR_INFO
        )
        await ctx.send(embed=embed)
    
    @bot.command(name='status')
    @is_admin_or_role()
    async def vps_status(ctx):
        """View all VPS status"""
        vps_list = run_in_thread(get_all_vps)
        
        if not vps_list:
            embed = discord.Embed(
                title="📊 VPS Status",
                description="No VPS found in the panel.",
                color=COLOR_INFO
            )
            await ctx.send(embed=embed)
            return
        
        running = sum(1 for v in vps_list if v.get('status') == 'running')
        stopped = sum(1 for v in vps_list if v.get('status') == 'stopped')
        suspended = sum(1 for v in vps_list if v.get('suspended'))
        
        embed = discord.Embed(
            title="📊 VPS Overview",
            description=f"**Total:** {len(vps_list)} | ✅ Running: {running} | ⏹ Stopped: {stopped} | 🚫 Suspended: {suspended}",
            color=COLOR_PRIMARY
        )
        
        # Group by node
        nodes = {}
        for v in vps_list:
            node_name = v.get('node_name', 'Unknown')
            if node_name not in nodes:
                nodes[node_name] = []
            nodes[node_name].append(v)
        
        for node_name, vps in nodes.items():
            running_n = sum(1 for v in vps if v.get('status') == 'running')
            stopped_n = sum(1 for v in vps if v.get('status') == 'stopped')
            suspended_n = sum(1 for v in vps if v.get('suspended'))
            
            lines = []
            for v in vps[:10]:  # Max 10 per node in display
                status_emoji = "✅" if v.get('status') == 'running' else "⏹"
                susp = " 🚫" if v.get('suspended') else ""
                owner = v.get('username', '?')
                lines.append(f"{status_emoji} `#{v['id']}` {v['container_name']} — {v['ram']}/{v['cpu']}CPU — @{owner}{susp}")
            
            if len(vps) > 10:
                lines.append(f"... and {len(vps) - 10} more")
            
            field_value = "\n".join(lines) if lines else "No VPS"
            if len(field_value) > 1024:
                field_value = field_value[:1020] + "..."
            
            embed.add_field(
                name=f"🖥️ {node_name} ({running_n}/{len(vps)} running, {suspended_n} suspended)",
                value=field_value,
                inline=False
            )
        
        embed.set_footer(text=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)
    
    @bot.command(name='vps')
    @is_admin_or_role()
    async def vps_detail(ctx, vps_id: int):
        """View detailed VPS info"""
        vps = run_in_thread(get_vps_by_id, vps_id)
        
        if not vps:
            embed = discord.Embed(title="❌ Not Found", description=f"VPS #{vps_id} not found.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        status_emoji = "✅" if vps.get('status') == 'running' else "⏹"
        susp = " 🚫 SUSPENDED" if vps.get('suspended') else ""
        
        features = []
        if vps.get('virt_kvm'):
            features.append("KVM")
        if vps.get('virt_docker'):
            features.append("Docker")
        feature_str = ", ".join(features) if features else "None"
        
        embed = discord.Embed(
            title=f"🖥️ VPS #{vps_id}: {vps.get('container_name')}",
            description=f"**Status:** {status_emoji} {vps.get('status', 'unknown')}{susp}",
            color=COLOR_PRIMARY
        )
        
        embed.add_field(name="👤 Owner", value=vps.get('username', 'Unknown'), inline=True)
        embed.add_field(name="🖥️ Node", value=vps.get('node_name', 'Unknown'), inline=True)
        embed.add_field(name="💻 OS", value=vps.get('os_version', 'Unknown'), inline=True)
        embed.add_field(name="🧠 CPU", value=f"{vps.get('cpu', '?')} cores", inline=True)
        embed.add_field(name="💾 RAM", value=vps.get('ram', '?'), inline=True)
        embed.add_field(name="💿 Storage", value=vps.get('storage', '?'), inline=True)
        embed.add_field(name="🔗 IP", value=vps.get('ip_address') or 'Not assigned', inline=True)
        embed.add_field(name="📦 Hostname", value=vps.get('hostname') or 'Not set', inline=True)
        embed.add_field(name="⚡ Virtualization", value=feature_str, inline=True)
        
        if vps.get('expires_at'):
            embed.add_field(name="⏰ Expires", value=vps['expires_at'][:10], inline=True)
        
        embed.set_footer(text=f"Container: {vps.get('container_name')}")
        await ctx.send(embed=embed)
    
    @bot.command(name='nodes')
    @is_admin_or_role()
    async def nodes_status(ctx):
        """View all node status"""
        nodes = run_in_thread(get_all_nodes)
        
        if not nodes:
            embed = discord.Embed(title="🖥️ Nodes", description="No nodes configured.", color=COLOR_INFO)
            await ctx.send(embed=embed)
            return
        
        embed = discord.Embed(title="🖥️ Node Status", color=COLOR_PRIMARY)
        
        for node in nodes:
            status = node.get('status', 'unknown')
            status_emoji = "✅" if status == 'online' else "❌" if status == 'offline' else "❓"
            vps_count = node.get('used_vps', 0)
            total_vps = node.get('total_vps', 50)
            
            fields = [
                f"**Status:** {status_emoji} {status}",
                f"**Location:** {node.get('location', 'Unknown')}",
                f"**VPS:** {vps_count}/{total_vps}",
                f"**Local:** {'Yes' if node.get('is_local') else 'No'}",
            ]
            
            if node.get('cpu_cores'):
                fields.append(f"**CPU:** {node['cpu_cores']} cores")
            if node.get('ram_total'):
                fields.append(f"**RAM:** {node['ram_total']}MB")
            
            embed.add_field(
                name=f"🖥️ {node['name']}",
                value="\n".join(fields),
                inline=True
            )
        
        await ctx.send(embed=embed)
    
    @bot.command(name='users')
    @is_admin_or_role()
    async def users_list(ctx):
        """List all users"""
        users = run_in_thread(get_all_users)
        
        embed = discord.Embed(title=f"👥 Users ({len(users)})", color=COLOR_PRIMARY)
        
        for user in users[:25]:  # Max 25 users in embed
            role = "👑 Main Admin" if user.get('is_main_admin') else "🛡️ Admin" if user.get('is_admin') else "👤 User"
            last_login = user.get('last_login', 'Never')
            if last_login and last_login != 'Never':
                last_login = last_login[:10]
            
            embed.add_field(
                name=f"#{user['id']} {user['username']}",
                value=f"{role}\n📧 {user.get('email', 'N/A')}\n🕐 Last login: {last_login}",
                inline=True
            )
        
        if len(users) > 25:
            embed.set_footer(text=f"Showing 25/{len(users)} users")
        
        await ctx.send(embed=embed)
    
    @bot.command(name='stats')
    @is_admin_or_role()
    async def panel_stats(ctx):
        """View panel statistics"""
        vps_list = run_in_thread(get_all_vps)
        users = run_in_thread(get_all_users)
        nodes = run_in_thread(get_all_nodes)
        
        total_vps = len(vps_list)
        running = sum(1 for v in vps_list if v.get('status') == 'running')
        stopped = sum(1 for v in vps_list if v.get('status') == 'stopped')
        suspended = sum(1 for v in vps_list if v.get('suspended'))
        
        total_users = len(users)
        admin_count = sum(1 for u in users if u.get('is_admin'))
        
        total_nodes = len(nodes)
        online_nodes = sum(1 for n in nodes if n.get('status') == 'online')
        
        total_ram = sum(int(v.get('ram', '0GB').replace('GB', '') or 0) for v in vps_list if v.get('status') == 'running')
        
        embed = discord.Embed(
            title="📊 QVM Panel Statistics",
            color=COLOR_PRIMARY
        )
        
        embed.add_field(
            name="🖥️ VPS",
            value=f"**Total:** {total_vps}\n✅ Running: {running}\n⏹ Stopped: {stopped}\n🚫 Suspended: {suspended}\n🧠 Total RAM (active): {total_ram}GB",
            inline=True
        )
        
        embed.add_field(
            name="👥 Users",
            value=f"**Total:** {total_users}\n🛡️ Admins: {admin_count}\n👤 Regular: {total_users - admin_count}",
            inline=True
        )
        
        embed.add_field(
            name="🖥️ Nodes",
            value=f"**Total:** {total_nodes}\n✅ Online: {online_nodes}\n❌ Offline: {total_nodes - online_nodes}",
            inline=True
        )
        
        embed.set_footer(text=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        await ctx.send(embed=embed)
    
    @bot.command(name='start')
    @is_admin_or_role()
    async def start_vps(ctx, vps_id: int):
        """Start a VPS"""
        vps = run_in_thread(get_vps_by_id, vps_id)
        if not vps:
            embed = discord.Embed(title="❌ Not Found", description=f"VPS #{vps_id} not found.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        if vps.get('suspended'):
            embed = discord.Embed(title="🚫 Suspended", description=f"VPS #{vps_id} is suspended.", color=COLOR_WARNING)
            await ctx.send(embed=embed)
            return
        
        if vps.get('status') == 'running':
            embed = discord.Embed(title="⚠️ Already Running", description=f"VPS #{vps_id} is already running.", color=COLOR_WARNING)
            await ctx.send(embed=embed)
            return
        
        msg = await ctx.send(embed=discord.Embed(title="⏳ Starting VPS...", description=f"Starting VPS #{vps_id} (`{vps['container_name']}`)...", color=COLOR_INFO))
        
        try:
            # Use the node agent API to start the container
            import requests as req
            node = get_db().cursor().execute('SELECT * FROM nodes WHERE id = ?', (vps['node_id'],)).fetchone()
            if node and node['url']:
                node = dict(node)
                headers = {"X-API-Key": node.get('api_key', '')}
                resp = req.post(f"{node['url']}/api/container/start", json={"container": vps['container_name']}, headers=headers, timeout=30)
                
                if resp.status_code == 200:
                    with get_db() as conn:
                        conn.cursor().execute("UPDATE vps SET status = 'running' WHERE id = ?", (vps_id,))
                        conn.commit()
                    
                    embed = discord.Embed(title="✅ VPS Started", description=f"VPS #{vps_id} (`{vps['container_name']}`) has been started.", color=COLOR_SUCCESS)
                    await msg.edit(embed=embed)
                    log_activity(ctx.author.id, 'discord_start_vps', {'vps_id': vps_id})
                else:
                    embed = discord.Embed(title="❌ Start Failed", description=f"Failed to start VPS: {resp.text[:200]}", color=COLOR_ERROR)
                    await msg.edit(embed=embed)
            else:
                embed = discord.Embed(title="❌ Node Offline", description="The node hosting this VPS is not configured or offline.", color=COLOR_ERROR)
                await msg.edit(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=f"Failed to start VPS: {str(e)[:200]}", color=COLOR_ERROR)
            await msg.edit(embed=embed)
    
    @bot.command(name='stop')
    @is_admin_or_role()
    async def stop_vps(ctx, vps_id: int):
        """Stop a VPS"""
        vps = run_in_thread(get_vps_by_id, vps_id)
        if not vps:
            embed = discord.Embed(title="❌ Not Found", description=f"VPS #{vps_id} not found.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        if vps.get('status') == 'stopped':
            embed = discord.Embed(title="⚠️ Already Stopped", description=f"VPS #{vps_id} is already stopped.", color=COLOR_WARNING)
            await ctx.send(embed=embed)
            return
        
        msg = await ctx.send(embed=discord.Embed(title="⏳ Stopping VPS...", description=f"Stopping VPS #{vps_id} (`{vps['container_name']}`)...", color=COLOR_INFO))
        
        try:
            import requests as req
            node = get_db().cursor().execute('SELECT * FROM nodes WHERE id = ?', (vps['node_id'],)).fetchone()
            if node and node['url']:
                node = dict(node)
                headers = {"X-API-Key": node.get('api_key', '')}
                resp = req.post(f"{node['url']}/api/container/stop", json={"container": vps['container_name']}, headers=headers, timeout=30)
                
                if resp.status_code == 200:
                    with get_db() as conn:
                        conn.cursor().execute("UPDATE vps SET status = 'stopped' WHERE id = ?", (vps_id,))
                        conn.commit()
                    
                    embed = discord.Embed(title="✅ VPS Stopped", description=f"VPS #{vps_id} (`{vps['container_name']}`) has been stopped.", color=COLOR_SUCCESS)
                    await msg.edit(embed=embed)
                    log_activity(ctx.author.id, 'discord_stop_vps', {'vps_id': vps_id})
                else:
                    embed = discord.Embed(title="❌ Stop Failed", description=f"Failed to stop VPS: {resp.text[:200]}", color=COLOR_ERROR)
                    await msg.edit(embed=embed)
            else:
                embed = discord.Embed(title="❌ Node Offline", description="The node hosting this VPS is not configured or offline.", color=COLOR_ERROR)
                await msg.edit(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=f"Failed to stop VPS: {str(e)[:200]}", color=COLOR_ERROR)
            await msg.edit(embed=embed)
    
    @bot.command(name='restart')
    @is_admin_or_role()
    async def restart_vps(ctx, vps_id: int):
        """Restart a VPS"""
        vps = run_in_thread(get_vps_by_id, vps_id)
        if not vps:
            embed = discord.Embed(title="❌ Not Found", description=f"VPS #{vps_id} not found.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        if vps.get('suspended'):
            embed = discord.Embed(title="🚫 Suspended", description=f"VPS #{vps_id} is suspended.", color=COLOR_WARNING)
            await ctx.send(embed=embed)
            return
        
        msg = await ctx.send(embed=discord.Embed(title="⏳ Restarting VPS...", description=f"Restarting VPS #{vps_id} (`{vps['container_name']}`)...", color=COLOR_INFO))
        
        try:
            import requests as req
            node = get_db().cursor().execute('SELECT * FROM nodes WHERE id = ?', (vps['node_id'],)).fetchone()
            if node and node['url']:
                node = dict(node)
                headers = {"X-API-Key": node.get('api_key', '')}
                resp = req.post(f"{node['url']}/api/container/restart", json={"container": vps['container_name']}, headers=headers, timeout=60)
                
                if resp.status_code == 200:
                    embed = discord.Embed(title="✅ VPS Restarted", description=f"VPS #{vps_id} (`{vps['container_name']}`) has been restarted.", color=COLOR_SUCCESS)
                    await msg.edit(embed=embed)
                    log_activity(ctx.author.id, 'discord_restart_vps', {'vps_id': vps_id})
                else:
                    embed = discord.Embed(title="❌ Restart Failed", description=f"Failed to restart VPS: {resp.text[:200]}", color=COLOR_ERROR)
                    await msg.edit(embed=embed)
            else:
                embed = discord.Embed(title="❌ Node Offline", description="The node hosting this VPS is not configured or offline.", color=COLOR_ERROR)
                await msg.edit(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="❌ Error", description=f"Failed to restart VPS: {str(e)[:200]}", color=COLOR_ERROR)
            await msg.edit(embed=embed)
    
    @bot.command(name='delete')
    @commands.has_permissions(administrator=True)
    async def delete_vps(ctx, vps_id: int):
        """Delete a VPS (admin only)"""
        vps = run_in_thread(get_vps_by_id, vps_id)
        if not vps:
            embed = discord.Embed(title="❌ Not Found", description=f"VPS #{vps_id} not found.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        # Confirmation
        embed = discord.Embed(
            title="⚠️ Confirm Deletion",
            description=f"Are you sure you want to delete VPS #{vps_id}?\n\n**Container:** `{vps['container_name']}`\n**Owner:** {vps.get('username', 'Unknown')}\n\nReact with ✅ to confirm or ❌ to cancel.",
            color=COLOR_WARNING
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            if str(reaction.emoji) == '❌':
                embed = discord.Embed(title="❌ Cancelled", description="VPS deletion cancelled.", color=COLOR_INFO)
                await msg.edit(embed=embed)
                return
        except asyncio.TimeoutError:
            embed = discord.Embed(title="⏰ Timeout", description="Deletion timed out. No changes made.", color=COLOR_WARNING)
            await msg.edit(embed=embed)
            return
        
        # Delete
        delete_msg = await ctx.send(embed=discord.Embed(title="⏳ Deleting VPS...", description=f"Deleting VPS #{vps_id}...", color=COLOR_INFO))
        
        try:
            # Delete from database
            with get_db() as conn:
                cur = conn.cursor()
                # Try to delete the container via node agent
                node = cur.execute('SELECT * FROM nodes WHERE id = ?', (vps['node_id'],)).fetchone()
                if node and node['url']:
                    import requests as req
                    node = dict(node)
                    headers = {"X-API-Key": node.get('api_key', '')}
                    try:
                        req.post(f"{node['url']}/api/container/stop", json={"container": vps['container_name']}, headers=headers, timeout=30)
                        req.post(f"{node['url']}/api/container/delete", json={"container": vps['container_name'], "force": True}, headers=headers, timeout=30)
                    except Exception:
                        pass
                
                cur.execute("DELETE FROM vps WHERE id = ?", (vps_id,))
                conn.commit()
            
            embed = discord.Embed(title="✅ VPS Deleted", description=f"VPS #{vps_id} (`{vps['container_name']}`) has been deleted.", color=COLOR_SUCCESS)
            await delete_msg.edit(embed=embed)
            log_activity(ctx.author.id, 'discord_delete_vps', {'vps_id': vps_id, 'container': vps['container_name']})
        except Exception as e:
            embed = discord.Embed(title="❌ Delete Failed", description=f"Failed to delete VPS: {str(e)[:200]}", color=COLOR_ERROR)
            await delete_msg.edit(embed=embed)
    
    @bot.command(name='deploy')
    @is_admin_or_role()
    async def deploy_vps(ctx):
        """Interactive VPS deployment wizard"""
        
        # Step 1: Get user
        users = run_in_thread(get_all_users)
        if not users:
            embed = discord.Embed(title="❌ No Users", description="No users found in the panel.", color=COLOR_ERROR)
            await ctx.send(embed=embed)
            return
        
        user_options = "\n".join([f"`{u['id']}` — {u['username']} ({u.get('email', 'N/A')})" for u in users[:15]])
        embed = discord.Embed(
            title="🚀 VPS Deployment — Step 1/4",
            description=f"**Select User ID:**\n\n{user_options}",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text="Type the user ID to continue. Send 'cancel' to abort.")
        await ctx.send(embed=embed)
        
        def msg_check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=msg_check)
            if msg.content.lower() == 'cancel':
                await ctx.send(embed=discord.Embed(title="❌ Cancelled", description="Deployment cancelled.", color=COLOR_INFO))
                return
            
            user_id = int(msg.content.strip())
            selected_user = next((u for u in users if u['id'] == user_id), None)
            if not selected_user:
                await ctx.send(embed=discord.Embed(title="❌ Invalid", description="User not found.", color=COLOR_ERROR))
                return
        except (ValueError, asyncio.TimeoutError):
            await ctx.send(embed=discord.Embed(title="⏰ Timeout", description="Deployment timed out.", color=COLOR_WARNING))
            return
        
        # Step 2: Select node
        nodes = run_in_thread(get_all_nodes)
        if not nodes:
            await ctx.send(embed=discord.Embed(title="❌ No Nodes", description="No nodes configured.", color=COLOR_ERROR))
            return
        
        node_options = "\n".join([f"`{n['id']}` — {n['name']} ({n.get('location', '?')}) [{n.get('used_vps', 0)}/{n.get('total_vps', 50)} VPS]" for n in nodes])
        embed = discord.Embed(
            title="🚀 VPS Deployment — Step 2/4",
            description=f"**Select Node ID for user `{selected_user['username']}`:**\n\n{node_options}",
            color=COLOR_PRIMARY
        )
        await ctx.send(embed=embed)
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=msg_check)
            if msg.content.lower() == 'cancel':
                await ctx.send(embed=discord.Embed(title="❌ Cancelled", description="Deployment cancelled.", color=COLOR_INFO))
                return
            
            node_id = int(msg.content.strip())
            selected_node = next((n for n in nodes if n['id'] == node_id), None)
            if not selected_node:
                await ctx.send(embed=discord.Embed(title="❌ Invalid", description="Node not found.", color=COLOR_ERROR))
                return
        except (ValueError, asyncio.TimeoutError):
            await ctx.send(embed=discord.Embed(title="⏰ Timeout", description="Deployment timed out.", color=COLOR_WARNING))
            return
        
        # Step 3: Resources
        os_options = [
            "Ubuntu 20.04 (ubuntu:20.04)", "Ubuntu 22.04 (ubuntu:22.04)", "Ubuntu 24.04 (ubuntu:24.04)",
            "Debian 11 (images:debian/11)", "Debian 12 (images:debian/12)", "Debian 13 (images:debian/13)"
        ]
        os_text = "\n".join([f"`{i+1}.` {o}" for i, o in enumerate(os_options)])
        
        embed = discord.Embed(
            title="🚀 VPS Deployment — Step 3/4",
            description=f"**Set resources for `{selected_node['name']}`:**\n\n{os_text}\n\nType in format:\n`<os_number> <cpu> <ram_gb> <disk_gb>`\nExample: `2 2 2 20` (Ubuntu 22.04, 2 CPU, 2GB RAM, 20GB Disk)",
            color=COLOR_PRIMARY
        )
        await ctx.send(embed=embed)
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=msg_check)
            if msg.content.lower() == 'cancel':
                await ctx.send(embed=discord.Embed(title="❌ Cancelled", description="Deployment cancelled.", color=COLOR_INFO))
                return
            
            parts = msg.content.strip().split()
            os_num = int(parts[0]) - 1
            cpu = int(parts[1])
            ram = int(parts[2])
            disk = int(parts[3])
            
            if os_num < 0 or os_num >= len(os_options):
                await ctx.send(embed=discord.Embed(title="❌ Invalid", description="Invalid OS selection.", color=COLOR_ERROR))
                return
            
            os_value = os_options[os_num].split('(')[1].rstrip(')')
            os_label = os_options[os_num].split('(')[0].strip()
        except (ValueError, IndexError, asyncio.TimeoutError):
            await ctx.send(embed=discord.Embed(title="⏰ Timeout/Invalid", description="Deployment timed out or invalid input.", color=COLOR_WARNING))
            return
        
        # Step 4: KVM/Docker options
        embed = discord.Embed(
            title="🚀 VPS Deployment — Step 4/4",
            description=f"**Virtualization options:**\n\nReply with:\n`kvm yes/no` then `docker yes/no`\n\nExample: `yes yes` (enable both KVM and Docker)\nType `cancel` to abort.",
            color=COLOR_PRIMARY
        )
        await ctx.send(embed=embed)
        
        try:
            msg = await bot.wait_for('message', timeout=60.0, check=msg_check)
            if msg.content.lower() == 'cancel':
                await ctx.send(embed=discord.Embed(title="❌ Cancelled", description="Deployment cancelled.", color=COLOR_INFO))
                return
            
            virt_parts = msg.content.strip().lower().split()
            kvm_enabled = virt_parts[0] == 'yes' if len(virt_parts) > 0 else False
            docker_enabled = virt_parts[1] == 'yes' if len(virt_parts) > 1 else False
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title="⏰ Timeout", description="Deployment timed out.", color=COLOR_WARNING))
            return
        
        # Confirm and deploy
        features = []
        if kvm_enabled:
            features.append("KVM")
        if docker_enabled:
            features.append("Docker")
        feature_str = ", ".join(features) if features else "None"
        
        embed = discord.Embed(
            title="📋 Deployment Summary",
            description=(
                f"**User:** {selected_user['username']} (#{user_id})\n"
                f"**Node:** {selected_node['name']}\n"
                f"**OS:** {os_label}\n"
                f"**CPU:** {cpu} cores | **RAM:** {ram}GB | **Disk:** {disk}GB\n"
                f"**Virtualization:** {feature_str}\n\n"
                f"React with ✅ to deploy or ❌ to cancel."
            ),
            color=COLOR_WARNING
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction('✅')
        await msg.add_reaction('❌')
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌']
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            if str(reaction.emoji) == '❌':
                await ctx.send(embed=discord.Embed(title="❌ Cancelled", description="Deployment cancelled.", color=COLOR_INFO))
                return
        except asyncio.TimeoutError:
            await ctx.send(embed=discord.Embed(title="⏰ Timeout", description="Deployment timed out.", color=COLOR_WARNING))
            return
        
        # Deploy
        deploy_msg = await ctx.send(embed=discord.Embed(title="⏳ Deploying VPS...", description="Creating VPS via panel API...", color=COLOR_INFO))
        
        try:
            import requests as req
            
            # Count existing VPS for this user
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute('SELECT COUNT(*) FROM vps WHERE user_id = ?', (user_id,))
                vps_count = cur.fetchone()[0] + 1
            
            container_name = f"avm-vps-{user_id}-{vps_count}"
            
            # Create via LXC commands
            from avm import run_sync, execute_lxc, apply_lxc_config, configure_container_ip, apply_internal_permissions, configure_ssh_and_root_password, DEFAULT_STORAGE_POOL
            
            ram_mb = ram * 1024
            
            run_sync(execute_lxc(container_name, f"init {os_value} {container_name} -s {DEFAULT_STORAGE_POOL}", node_id=node_id))
            run_sync(execute_lxc(container_name, f"config set {container_name} limits.memory {ram_mb}MB", node_id=node_id))
            run_sync(execute_lxc(container_name, f"config set {container_name} limits.cpu {cpu}", node_id=node_id))
            run_sync(execute_lxc(container_name, f"config device set {container_name} root size={disk}GB", node_id=node_id))
            
            run_sync(apply_lxc_config(container_name, node_id))
            
            if kvm_enabled:
                try:
                    run_sync(execute_lxc(container_name, f"config set {container_name} security.privileged true", node_id=node_id))
                    run_sync(execute_lxc(container_name, f"config set {container_name} security.nesting true", node_id=node_id))
                    try:
                        run_sync(execute_lxc(container_name, f"config device add {container_name} kvm unix-char path=/dev/kvm", node_id=node_id))
                    except Exception:
                        pass
                except Exception as e:
                    logger.error(f"KVM config error: {e}")
            
            if docker_enabled:
                try:
                    run_sync(execute_lxc(container_name, f"config set {container_name} security.nesting true", node_id=node_id))
                    run_sync(execute_lxc(container_name, f"config set {container_name} security.privileged true", node_id=node_id))
                except Exception as e:
                    logger.error(f"Docker config error: {e}")
            
            run_sync(execute_lxc(container_name, f"start {container_name}", node_id=node_id))
            run_sync(apply_internal_permissions(container_name, node_id))
            run_sync(configure_ssh_and_root_password(container_name, node_id))
            
            # Apply QVM Panel branding
            branding_script = (
                "mkdir -p ~/.config/fastfetch ~/.config/neofetch && "
                "cat > ~/.config/fastfetch/config.jsonc <<'BRANDEOF'\n"
                "{\"modules\":[\"title\",\"separator\",\"os\",{\"type\":\"host\",\"format\":\"QVM Panel\"},\"kernel\",\"uptime\",\"packages\",\"shell\",\"cpu\",\"memory\",\"disk\",\"localip\",\"locale\",\"colors\"]}\n"
                "BRANDEOF\n"
                "neofetch --print_config > ~/.config/neofetch/config.conf 2>/dev/null && "
                "sed -i 's/info \"Host\".*/prin \"Host\" \"QVM Panel\"/' ~/.config/neofetch/config.conf && "
                "echo 'Branding applied.'"
            )
            try:
                run_sync(execute_lxc(container_name, f"exec {container_name} -- sh -c \"{branding_script}\"", node_id=node_id, timeout=30))
            except Exception:
                pass
            
            # Create DB record
            features_list = []
            if kvm_enabled:
                features_list.append("KVM")
            if docker_enabled:
                features_list.append("Docker")
            feat_str = f" + {', '.join(features_list)}" if features_list else ""
            config_str = f"{ram}GB RAM / {cpu} CPU / {disk}GB Disk{feat_str}"
            
            now = datetime.now().isoformat()
            with get_db() as conn:
                cur = conn.cursor()
                cur.execute('''INSERT INTO vps 
                    (user_id, node_id, container_name, hostname, ram, cpu, storage, config, os_version,
                     status, created_at, updated_at, virt_kvm, virt_docker)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, node_id, container_name, container_name, f"{ram}GB", str(cpu), f"{disk}GB",
                     config_str, os_value, 'running', now, now, 1 if kvm_enabled else 0, 1 if docker_enabled else 0))
                conn.commit()
            
            # Notify user
            create_notification(user_id, 'success', 'VPS Deployed via Discord', f'Your VPS {container_name} has been deployed.')
            
            features = []
            if kvm_enabled:
                features.append("KVM 🖥️")
            if docker_enabled:
                features.append("Docker 🐳")
            feat_str = f"\n**Features:** {', '.join(features)}" if features else ""
            
            embed = discord.Embed(
                title="✅ VPS Deployed Successfully!",
                description=(
                    f"**Container:** `{container_name}`\n"
                    f"**User:** {selected_user['username']}\n"
                    f"**Node:** {selected_node['name']}\n"
                    f"**OS:** {os_label}\n"
                    f"**Specs:** {ram}GB RAM / {cpu} CPU / {disk}GB Disk{feat_str}\n"
                    f"**Status:** ✅ Running\n\n"
                    f"🔗 Panel: {PANEL_URL}"
                ),
                color=COLOR_SUCCESS
            )
            await deploy_msg.edit(embed=embed)
            log_activity(ctx.author.id, 'discord_deploy_vps', {'user_id': user_id, 'container': container_name})
            
        except Exception as e:
            logger.error(f"Deploy error: {e}", exc_info=True)
            embed = discord.Embed(title="❌ Deployment Failed", description=f"Error: {str(e)[:300]}", color=COLOR_ERROR)
            await deploy_msg.edit(embed=embed)
    
    # ─── Slash Commands ───────────────────────────────────
    
    @bot.tree.command(name="status", description="View all VPS status overview")
    @app_commands.describe()
    async def slash_status(interaction: discord.Interaction):
        if not (interaction.user.guild_permissions.administrator or
                (get_setting('discord_bot_deploy_role', '') and 
                 any(r.id == int(get_setting('discord_bot_deploy_role', '0')) for r in interaction.user.roles if get_setting('discord_bot_deploy_role', '')))):
            await interaction.response.send_message("❌ You don't have permission.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        vps_list = await asyncio.to_thread(get_all_vps)
        
        if not vps_list:
            embed = discord.Embed(title="📊 VPS Status", description="No VPS found.", color=COLOR_INFO)
            await interaction.followup.send(embed=embed)
            return
        
        running = sum(1 for v in vps_list if v.get('status') == 'running')
        stopped = sum(1 for v in vps_list if v.get('status') == 'stopped')
        suspended = sum(1 for v in vps_list if v.get('suspended'))
        
        embed = discord.Embed(
            title="📊 VPS Overview",
            description=f"**Total:** {len(vps_list)} | ✅ Running: {running} | ⏹ Stopped: {stopped} | 🚫 Suspended: {suspended}",
            color=COLOR_PRIMARY
        )
        
        await interaction.followup.send(embed=embed)
    
    @bot.tree.command(name="deploy", description="Deploy a new VPS interactively")
    async def slash_deploy(interaction: discord.Interaction):
        await interaction.response.send_message("🚀 Starting deployment wizard...\nUse `!deploy` in a channel to use the interactive wizard.", ephemeral=True)
    
    return bot


# ─── Main ─────────────────────────────────────────────────
def main():
    if not DISCORD_AVAILABLE:
        print("ERROR: discord.py is not installed.")
        print("Run: pip install discord.py")
        sys.exit(1)
    
    # Get bot token from database or env
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token:
        bot_token = get_setting('discord_bot_token', '')
    
    if not bot_token:
        print("ERROR: No bot token configured!")
        print("Set DISCORD_BOT_TOKEN environment variable or configure it in admin settings.")
        sys.exit(1)
    
    bot_enabled = get_setting('discord_bot_enabled', '0')
    if bot_enabled != '1' and not os.getenv('DISCORD_BOT_TOKEN'):
        print("Discord bot is disabled in settings. Enable it in admin panel or set DISCORD_BOT_TOKEN env var.")
        sys.exit(0)
    
    bot = create_bot()
    
    print("=" * 60)
    print("  QVM Panel Discord Bot v1.0")
    print("  Developer: QVM Panel")
    print("=" * 60)
    print(f"  Starting bot...")
    print(f"  Panel URL: {PANEL_URL}")
    print(f"  Database: {DATABASE_PATH}")
    print("=" * 60)
    
    bot.run(bot_token)


if __name__ == '__main__':
    main()
