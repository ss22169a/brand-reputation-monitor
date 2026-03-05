"""
Alert Rules Engine API
Manages auto-alerting rules and notifications
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

# Path to alert rules
ALERTS_PATH = Path(__file__).parent.parent.parent / 'data' / 'alert_rules.json'


class RuleConfig(BaseModel):
    """Alert rule configuration"""
    days: Optional[int] = None
    consecutive_days: Optional[int] = None
    threshold: Optional[int] = None
    risk_threshold: Optional[int] = None
    count: Optional[int] = None
    keywords: Optional[List[str]] = None
    monitor_brands: Optional[List[str]] = None
    metric: Optional[str] = None
    hours: Optional[int] = None
    regions: Optional[List[str]] = None
    percentage: Optional[int] = None


class NotificationConfig(BaseModel):
    """Notification settings"""
    channels: List[str] = ["dashboard"]  # dashboard, email, sms, push
    priority: str = "medium"  # low, medium, high, critical


class AlertRule(BaseModel):
    """Alert rule model"""
    id: str
    name: str
    type: str
    enabled: bool
    config: Dict[str, Any]
    notification: Dict[str, Any]
    description: str


def load_rules() -> Dict[str, Any]:
    """Load alert rules from JSON"""
    if not ALERTS_PATH.exists():
        return {"rules": [], "alert_history": []}
    try:
        with open(ALERTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading rules: {e}")
        return {"rules": [], "alert_history": []}


def save_rules(data: Dict[str, Any]) -> bool:
    """Save alert rules"""
    try:
        ALERTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        data['metadata']['lastUpdated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(ALERTS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving rules: {e}")
        return False


def log_alert(rules_data: Dict[str, Any], rule_id: str, alert_message: str, severity: str = "warning"):
    """Log alert event to history"""
    alert_event = {
        "timestamp": datetime.now().isoformat(),
        "rule_id": rule_id,
        "message": alert_message,
        "severity": severity
    }
    if "alert_history" not in rules_data:
        rules_data["alert_history"] = []
    rules_data["alert_history"].append(alert_event)
    # Keep only last 1000 alerts
    if len(rules_data["alert_history"]) > 1000:
        rules_data["alert_history"] = rules_data["alert_history"][-1000:]


# Routes

@router.get("/rules")
async def get_all_rules():
    """Get all alert rules"""
    data = load_rules()
    return data.get("rules", [])


@router.get("/rules/{rule_id}")
async def get_rule(rule_id: str):
    """Get specific rule"""
    data = load_rules()
    for rule in data.get("rules", []):
        if rule["id"] == rule_id:
            return rule
    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@router.post("/rules")
async def create_rule(rule: AlertRule):
    """Create new rule"""
    data = load_rules()
    
    # Check if rule ID already exists
    for existing in data.get("rules", []):
        if existing["id"] == rule.id:
            raise HTTPException(status_code=409, detail=f"Rule {rule.id} already exists")
    
    new_rule = {
        "id": rule.id,
        "name": rule.name,
        "type": rule.type,
        "enabled": rule.enabled,
        "config": rule.config,
        "notification": rule.notification,
        "description": rule.description,
        "created_at": datetime.now().isoformat()
    }
    
    data["rules"].append(new_rule)
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error saving rule")
    
    return {"message": "Rule created", "rule": new_rule}


@router.put("/rules/{rule_id}")
async def update_rule(rule_id: str, rule_update: Dict[str, Any]):
    """Update existing rule"""
    data = load_rules()
    
    rule_found = False
    for i, rule in enumerate(data.get("rules", [])):
        if rule["id"] == rule_id:
            data["rules"][i].update(rule_update)
            data["rules"][i]["updated_at"] = datetime.now().isoformat()
            rule_found = True
            break
    
    if not rule_found:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error updating rule")
    
    return {"message": "Rule updated", "rule": data["rules"][i]}


@router.delete("/rules/{rule_id}")
async def delete_rule(rule_id: str):
    """Delete rule"""
    data = load_rules()
    
    original_count = len(data.get("rules", []))
    data["rules"] = [r for r in data.get("rules", []) if r["id"] != rule_id]
    
    if len(data["rules"]) == original_count:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error deleting rule")
    
    return {"message": f"Rule {rule_id} deleted"}


@router.post("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: str):
    """Enable/disable rule"""
    data = load_rules()
    
    for rule in data.get("rules", []):
        if rule["id"] == rule_id:
            rule["enabled"] = not rule["enabled"]
            if not save_rules(data):
                raise HTTPException(status_code=500, detail="Error updating rule")
            return {"message": "Rule toggled", "rule_id": rule_id, "enabled": rule["enabled"]}
    
    raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")


@router.get("/history")
async def get_alert_history(limit: int = 50):
    """Get alert history"""
    data = load_rules()
    history = data.get("alert_history", [])
    return history[-limit:]


@router.delete("/history")
async def clear_alert_history():
    """Clear all alert history"""
    data = load_rules()
    data["alert_history"] = []
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error clearing history")
    
    return {"message": "Alert history cleared"}


@router.post("/test/{rule_id}")
async def test_rule(rule_id: str):
    """Test rule (trigger mock alert)"""
    data = load_rules()
    
    rule = None
    for r in data.get("rules", []):
        if r["id"] == rule_id:
            rule = r
            break
    
    if not rule:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    # Log test alert
    alert_message = f"[TEST] {rule['name']} - 規則測試觸發"
    log_alert(data, rule_id, alert_message, "test")
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error logging test alert")
    
    return {
        "message": "Rule test triggered",
        "rule_id": rule_id,
        "rule_name": rule["name"],
        "alert": {
            "timestamp": datetime.now().isoformat(),
            "message": alert_message,
            "severity": "test"
        }
    }


@router.post("/trigger")
async def trigger_alert(rule_id: str, message: str, severity: str = "warning"):
    """Trigger alert manually (for internal use)"""
    data = load_rules()
    
    # Verify rule exists
    rule_found = any(r["id"] == rule_id for r in data.get("rules", []))
    
    if not rule_found:
        raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
    
    log_alert(data, rule_id, message, severity)
    
    if not save_rules(data):
        raise HTTPException(status_code=500, detail="Error logging alert")
    
    return {
        "message": "Alert triggered",
        "alert": {
            "timestamp": datetime.now().isoformat(),
            "rule_id": rule_id,
            "severity": severity,
            "message": message
        }
    }


@router.get("/stats")
async def get_alert_stats():
    """Get alert statistics"""
    data = load_rules()
    rules = data.get("rules", [])
    history = data.get("alert_history", [])
    
    enabled_count = sum(1 for r in rules if r["enabled"])
    recent_alerts = history[-20:] if history else []
    
    # Count by severity
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "test": 0}
    for alert in recent_alerts:
        severity = alert.get("severity", "medium")
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    return {
        "total_rules": len(rules),
        "enabled_rules": enabled_count,
        "disabled_rules": len(rules) - enabled_count,
        "total_alerts": len(history),
        "recent_alerts_count": len(recent_alerts),
        "severity_distribution": severity_counts
    }
