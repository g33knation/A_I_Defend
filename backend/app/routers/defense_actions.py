"""
Defense Actions Router - Manages autonomous defensive actions
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

router = APIRouter(prefix="/api/defense", tags=["defense"])


class DefenseActionRequest(BaseModel):
    action_type: str  # block_ip, quarantine_file, kill_process, alert
    target: str       # IP address, file path, or PID
    reason: str
    executed_by: str = "manual"
    metadata: Dict[str, Any] = {}


class DefenseConfigUpdate(BaseModel):
    key: str
    value: Any


# In-memory cache for defense config (refreshed from DB)
defense_config_cache = {}


async def get_db_pool():
    """Get database pool from app state."""
    from fastapi import Request
    # This will be injected by the main app
    pass


@router.get("/actions")
async def list_defense_actions(status: Optional[str] = None, limit: int = 50):
    """List defense actions taken by the system."""
    from app.main import app
    try:
        async with app.state.pool.acquire() as conn:
            if status:
                rows = await conn.fetch("""
                    SELECT da.*, e.type as event_type, d.summary as detection_summary
                    FROM defense_actions da
                    LEFT JOIN events e ON da.trigger_event_id = e.id
                    LEFT JOIN detections d ON da.trigger_detection_id = d.id
                    WHERE da.status = $1
                    ORDER BY da.created_at DESC
                    LIMIT $2
                """, status, limit)
            else:
                rows = await conn.fetch("""
                    SELECT da.*, e.type as event_type, d.summary as detection_summary
                    FROM defense_actions da
                    LEFT JOIN events e ON da.trigger_event_id = e.id
                    LEFT JOIN detections d ON da.trigger_detection_id = d.id
                    ORDER BY da.created_at DESC
                    LIMIT $1
                """, limit)
            return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error listing defense actions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions")
async def create_defense_action(action: DefenseActionRequest):
    """Execute and record a defense action."""
    from app.main import app
    from app.routers import agents
    
    valid_actions = ['block_ip', 'unblock_ip', 'quarantine_file', 'restore_file', 'kill_process', 'alert']
    if action.action_type not in valid_actions:
        raise HTTPException(status_code=400, detail=f"Invalid action_type. Must be one of: {valid_actions}")
    
    try:
        # Find defense agent to execute the action
        defense_agent_id = None
        if agents.agents:
            for agent_id, agent in agents.agents.items():
                if 'defense' in agent.get('capabilities', []) or 'block-ip' in agent.get('capabilities', []):
                    defense_agent_id = agent_id
                    break
        
        # Record the action in database
        async with app.state.pool.acquire() as conn:
            action_id = await conn.fetchval("""
                INSERT INTO defense_actions (action_type, target, reason, executed_by, metadata, status)
                VALUES ($1, $2, $3, $4, $5, 'pending')
                RETURNING id
            """, action.action_type, action.target, action.reason, action.executed_by, json.dumps(action.metadata))
            
            # If we have a defense agent, assign the action to it
            execution_result = {"status": "pending", "message": "Action recorded"}
            
            if defense_agent_id and action.action_type in ['block_ip', 'unblock_ip', 'quarantine_file', 'restore_file', 'kill_process']:
                # Assign action to defense agent
                agents.agent_assignments[defense_agent_id] = {
                    "assignment_id": f"defense-{action_id}",
                    "action_type": action.action_type,
                    "target": action.target,
                    "reason": action.reason,
                    "defense_action_id": action_id,
                    "assigned_at": datetime.utcnow().isoformat()
                }
                execution_result = {"status": "assigned", "message": f"Action assigned to defense agent", "agent_id": defense_agent_id}
                
                # Update status to assigned
                await conn.execute("""
                    UPDATE defense_actions SET status = 'assigned', metadata = $1 WHERE id = $2
                """, json.dumps({**action.metadata, "agent_id": defense_agent_id}), action_id)
            
            elif action.action_type == 'alert':
                # Alerts are just logged, no agent needed
                await conn.execute("""
                    UPDATE defense_actions SET status = 'active' WHERE id = $1
                """, action_id)
                execution_result = {"status": "active", "message": "Alert logged"}
            
            else:
                # No defense agent available
                execution_result = {"status": "pending", "message": "No defense agent available to execute action"}
            
            return {
                "action_id": action_id,
                "action_type": action.action_type,
                "target": action.target,
                **execution_result
            }
            
    except Exception as e:
        print(f"Error creating defense action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/actions/{action_id}/rollback")
async def rollback_defense_action(action_id: int):
    """Rollback a specific defense action."""
    from app.main import app
    from app.routers import agents
    
    try:
        async with app.state.pool.acquire() as conn:
            # Get the action
            action = await conn.fetchrow("""
                SELECT * FROM defense_actions WHERE id = $1
            """, action_id)
            
            if not action:
                raise HTTPException(status_code=404, detail="Action not found")
            
            if action['status'] == 'rolled_back':
                raise HTTPException(status_code=400, detail="Action already rolled back")
            
            # Determine the inverse action
            inverse_actions = {
                'block_ip': 'unblock_ip',
                'quarantine_file': 'restore_file',
            }
            
            if action['action_type'] not in inverse_actions:
                raise HTTPException(status_code=400, detail=f"Cannot rollback action type: {action['action_type']}")
            
            inverse_action_type = inverse_actions[action['action_type']]
            
            # Find defense agent
            defense_agent_id = None
            if agents.agents:
                for agent_id, agent in agents.agents.items():
                    if 'defense' in agent.get('capabilities', []) or 'block-ip' in agent.get('capabilities', []):
                        defense_agent_id = agent_id
                        break
            
            # Create rollback action
            rollback_id = await conn.fetchval("""
                INSERT INTO defense_actions (action_type, target, reason, executed_by, metadata, status)
                VALUES ($1, $2, $3, 'rollback', $4, 'pending')
                RETURNING id
            """, inverse_action_type, action['target'], f"Rollback of action #{action_id}", 
                json.dumps({"original_action_id": action_id}))
            
            # Mark original as rolled back
            await conn.execute("""
                UPDATE defense_actions SET status = 'rolled_back', rolled_back_at = NOW() WHERE id = $1
            """, action_id)
            
            # Assign to agent if available
            if defense_agent_id:
                agents.agent_assignments[defense_agent_id] = {
                    "assignment_id": f"defense-{rollback_id}",
                    "action_type": inverse_action_type,
                    "target": action['target'],
                    "reason": f"Rollback of action #{action_id}",
                    "defense_action_id": rollback_id,
                    "assigned_at": datetime.utcnow().isoformat()
                }
            
            return {
                "message": f"Rollback initiated for action #{action_id}",
                "rollback_action_id": rollback_id,
                "inverse_action": inverse_action_type,
                "target": action['target']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error rolling back defense action: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_defense_config():
    """Get all defense configuration."""
    from app.main import app
    try:
        async with app.state.pool.acquire() as conn:
            rows = await conn.fetch("SELECT key, value, description FROM defense_config")
            config = {}
            for row in rows:
                try:
                    config[row['key']] = {
                        "value": json.loads(row['value']) if isinstance(row['value'], str) else row['value'],
                        "description": row['description']
                    }
                except json.JSONDecodeError:
                    config[row['key']] = {"value": row['value'], "description": row['description']}
            return config
    except Exception as e:
        print(f"Error getting defense config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_defense_config(update: DefenseConfigUpdate):
    """Update a defense configuration value."""
    from app.main import app
    try:
        async with app.state.pool.acquire() as conn:
            # Check if key exists
            existing = await conn.fetchval("SELECT key FROM defense_config WHERE key = $1", update.key)
            if not existing:
                raise HTTPException(status_code=404, detail=f"Config key '{update.key}' not found")
            
            # Update the value
            value_json = json.dumps(update.value) if not isinstance(update.value, str) else f'"{update.value}"'
            await conn.execute("""
                UPDATE defense_config SET value = $1, updated_at = NOW() WHERE key = $2
            """, value_json, update.key)
            
            return {"message": f"Config '{update.key}' updated", "new_value": update.value}
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating defense config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_defense_stats():
    """Get defense statistics summary."""
    from app.main import app
    try:
        async with app.state.pool.acquire() as conn:
            # Get counts by action type and status
            stats = await conn.fetch("""
                SELECT action_type, status, COUNT(*) as count
                FROM defense_actions
                GROUP BY action_type, status
            """)
            
            # Get recent activity
            recent = await conn.fetchval("""
                SELECT COUNT(*) FROM defense_actions WHERE created_at > NOW() - INTERVAL '24 hours'
            """)
            
            # Get active blocks
            active_blocks = await conn.fetchval("""
                SELECT COUNT(*) FROM defense_actions 
                WHERE action_type = 'block_ip' AND status = 'active'
            """)
            
            return {
                "by_type_status": [dict(s) for s in stats],
                "actions_last_24h": recent,
                "active_ip_blocks": active_blocks
            }
            
    except Exception as e:
        print(f"Error getting defense stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def trigger_autonomous_defense(event_id: int, detection_id: int, score: float, 
                                     event_type: str, payload: dict, pool):
    """
    Called when a high-severity detection occurs to trigger autonomous defense.
    Only triggers if score >= configured threshold (default 0.9).
    """
    try:
        async with pool.acquire() as conn:
            # Get defense config
            config_row = await conn.fetchrow("""
                SELECT value FROM defense_config WHERE key = 'autonomous_defense_enabled'
            """)
            if config_row:
                enabled = json.loads(config_row['value']) if isinstance(config_row['value'], str) else config_row['value']
                if not enabled:
                    print("Autonomous defense is disabled")
                    return None
            
            # Get severity threshold
            threshold_row = await conn.fetchrow("""
                SELECT value FROM defense_config WHERE key = 'severity_threshold'
            """)
            threshold = 0.9
            if threshold_row:
                try:
                    threshold = float(json.loads(threshold_row['value']))
                except:
                    threshold = 0.9
            
            if score < threshold:
                print(f"Score {score} below threshold {threshold}, skipping autonomous defense")
                return None
            
            # Get enabled actions
            actions_row = await conn.fetchrow("""
                SELECT value FROM defense_config WHERE key = 'enabled_actions'
            """)
            enabled_actions = ['block_ip', 'quarantine_file', 'alert']
            if actions_row:
                try:
                    enabled_actions = json.loads(actions_row['value'])
                except:
                    pass
            
            print(f"⚡ AUTONOMOUS DEFENSE TRIGGERED: score={score}, event={event_type}")
            
            # Determine appropriate action based on event type
            action_to_take = None
            target = None
            reason = None
            
            if event_type in ['malware_detected', 'clamav_scan', 'yara_scan']:
                # Quarantine malware files
                if 'quarantine_file' in enabled_actions:
                    details = payload.get('details', {})
                    infected_files = details.get('infected_files', [])
                    if infected_files:
                        action_to_take = 'quarantine_file'
                        target = infected_files[0]  # First infected file
                        reason = f"Malware detected: {event_type}"
            
            elif event_type in ['port_scan', 'nmap_scan', 'masscan_scan']:
                # Block IP of scanner
                if 'block_ip' in enabled_actions:
                    details = payload.get('details', {})
                    # Try to extract scanner IP from payload
                    scanner_ip = details.get('scanner_ip') or details.get('source_ip') or payload.get('ip')
                    if scanner_ip:
                        action_to_take = 'block_ip'
                        target = scanner_ip
                        reason = f"Port scan detected: {event_type}"
            
            elif event_type in ['ids_alert', 'suricata_scan']:
                # Block attacker IP
                if 'block_ip' in enabled_actions:
                    details = payload.get('details', {})
                    alerts = details.get('alerts', [])
                    if alerts and isinstance(alerts[0], dict):
                        attacker_ip = alerts[0].get('src_ip') or alerts[0].get('source_ip')
                        if attacker_ip:
                            action_to_take = 'block_ip'
                            target = attacker_ip
                            reason = f"IDS alert: {alerts[0].get('signature', 'Unknown threat')}"
            
            # Always create an alert
            if 'alert' in enabled_actions and not action_to_take:
                action_to_take = 'alert'
                target = event_type
                reason = f"High-severity detection: score {score}"
            
            if action_to_take and target:
                # Record the autonomous defense action
                action_id = await conn.fetchval("""
                    INSERT INTO defense_actions 
                    (action_type, target, reason, trigger_event_id, trigger_detection_id, executed_by, status)
                    VALUES ($1, $2, $3, $4, $5, 'autonomous', 'pending')
                    RETURNING id
                """, action_to_take, target, reason, event_id, detection_id)
                
                print(f"🛡️ Created defense action #{action_id}: {action_to_take} -> {target}")
                
                return {
                    "action_id": action_id,
                    "action_type": action_to_take,
                    "target": target,
                    "reason": reason
                }
            
            return None
            
    except Exception as e:
        print(f"Error in autonomous defense: {e}")
        return None
