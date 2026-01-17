"""
Cost Guard Automation - Cloud Function
Version: 1.0
Purpose: Monitor budget thresholds, send alerts, auto-pause agents at 100% utilization

Triggered by:
1. Pub/Sub messages from OPA decision logs (budget threshold breaches)
2. Cloud Scheduler (daily budget reports at 9 AM UTC)
3. HTTP endpoint (manual trigger for testing)

Environment Variables:
- REDIS_URL: Redis connection string
- SLACK_WEBHOOK_URL: Slack incoming webhook for alerts
- SENDGRID_API_KEY: SendGrid API key for email notifications
- PLANT_API_URL: Plant backend URL (for pausing agents)
- PLANT_API_KEY: Plant API authentication key
- ALERT_EMAIL_RECIPIENTS: Comma-separated list of email addresses
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import redis
import requests
from google.cloud import logging as cloud_logging
from google.cloud import monitoring_v3
import functions_framework
from flask import Request, jsonify

# Configure logging
cloud_logging_client = cloud_logging.Client()
cloud_logging_client.setup_logging()
logger = logging.getLogger(__name__)

# Environment configuration
REDIS_URL = os.environ.get("REDIS_URL")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
PLANT_API_URL = os.environ.get("PLANT_API_URL", "https://plant.waooaw.com")
PLANT_API_KEY = os.environ.get("PLANT_API_KEY")
ALERT_EMAIL_RECIPIENTS = os.environ.get("ALERT_EMAIL_RECIPIENTS", "").split(",")

# Redis client (lazy initialization)
_redis_client: Optional[redis.Redis] = None

def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client


def get_budget_status() -> Dict:
    """
    Query Redis for current budget status.
    
    Returns:
        {
            "platform": {
                "spent_usd": 87.50,
                "cap_usd": 100.00,
                "utilization_percent": 87.5,
                "alert_level": "warning"
            },
            "agents": [
                {
                    "agent_id": "agent_001",
                    "spent_usd": 0.95,
                    "cap_usd": 1.00,
                    "alert_level": "high"
                },
                ...
            ]
        }
    """
    r = get_redis_client()
    
    # Get platform budget
    platform_budget = r.hgetall("platform_budget")
    spent_usd = float(platform_budget.get("spent_usd", 0.0))
    cap_usd = 100.00  # Constitutional limit
    utilization = (spent_usd / cap_usd) * 100
    
    # Determine alert level
    if utilization >= 100:
        alert_level = "critical"
    elif utilization >= 95:
        alert_level = "high"
    elif utilization >= 80:
        alert_level = "warning"
    else:
        alert_level = "normal"
    
    platform_status = {
        "spent_usd": spent_usd,
        "cap_usd": cap_usd,
        "utilization_percent": round(utilization, 2),
        "alert_level": alert_level,
        "last_reset_at": platform_budget.get("last_reset_at")
    }
    
    # Get per-agent budgets
    agent_keys = r.keys("agent_budgets:*")
    agents_status = []
    
    for key in agent_keys:
        agent_id = key.split(":")[-1]
        agent_budget = r.hgetall(key)
        agent_spent = float(agent_budget.get("spent_usd", 0.0))
        agent_cap = 1.00  # Constitutional limit per agent per day
        agent_utilization = (agent_spent / agent_cap) * 100
        
        # Determine agent alert level
        if agent_utilization >= 100:
            agent_alert_level = "critical"
        elif agent_utilization >= 95:
            agent_alert_level = "high"
        elif agent_utilization >= 80:
            agent_alert_level = "warning"
        else:
            agent_alert_level = "normal"
        
        if agent_alert_level != "normal":  # Only include agents with alerts
            agents_status.append({
                "agent_id": agent_id,
                "spent_usd": agent_spent,
                "cap_usd": agent_cap,
                "utilization_percent": round(agent_utilization, 2),
                "alert_level": agent_alert_level,
                "last_reset_at": agent_budget.get("last_reset_at")
            })
    
    # Sort agents by utilization (highest first)
    agents_status.sort(key=lambda x: x["utilization_percent"], reverse=True)
    
    return {
        "platform": platform_status,
        "agents": agents_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def send_slack_alert(budget_status: Dict) -> None:
    """
    Send Slack notification for budget threshold breach.
    
    Args:
        budget_status: Budget status from get_budget_status()
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping Slack alert")
        return
    
    platform = budget_status["platform"]
    agents = budget_status["agents"]
    alert_level = platform["alert_level"]
    
    # Color coding based on alert level
    color_map = {
        "warning": "#FFA500",  # Orange
        "high": "#FF4500",     # Red-Orange
        "critical": "#FF0000"  # Red
    }
    color = color_map.get(alert_level, "#808080")
    
    # Build Slack message
    text = f"⚠️ *Budget Alert: {alert_level.upper()}*\n\n"
    text += f"*Platform Budget*\n"
    text += f"• Spent: ${platform['spent_usd']:.2f} / ${platform['cap_usd']:.2f}\n"
    text += f"• Utilization: {platform['utilization_percent']:.1f}%\n"
    text += f"• Alert Level: {alert_level}\n\n"
    
    if agents:
        text += f"*Agents Exceeding Thresholds* ({len(agents)}):\n"
        for agent in agents[:5]:  # Show top 5 agents
            text += f"• `{agent['agent_id']}`: ${agent['spent_usd']:.2f} ({agent['utilization_percent']:.1f}%) - {agent['alert_level']}\n"
        
        if len(agents) > 5:
            text += f"• ... and {len(agents) - 5} more agents\n"
    
    if alert_level == "critical":
        text += "\n🚨 *Action Required*: Platform budget at 100%. All agents will be auto-paused.\n"
    elif alert_level == "high":
        text += "\n⚠️ *Action Recommended*: Platform budget at 95%. Consider pausing non-critical agents.\n"
    
    payload = {
        "attachments": [{
            "color": color,
            "text": text,
            "footer": "WAOOAW Cost Guard",
            "ts": int(datetime.now(timezone.utc).timestamp())
        }]
    }
    
    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logger.info("Slack alert sent successfully")
    except requests.RequestException as e:
        logger.error(f"Failed to send Slack alert: {e}")


def send_email_alert(budget_status: Dict) -> None:
    """
    Send email notification for budget threshold breach using SendGrid.
    
    Args:
        budget_status: Budget status from get_budget_status()
    """
    if not SENDGRID_API_KEY or not ALERT_EMAIL_RECIPIENTS:
        logger.warning("SendGrid not configured, skipping email alert")
        return
    
    platform = budget_status["platform"]
    agents = budget_status["agents"]
    alert_level = platform["alert_level"]
    
    # Build email HTML
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .header {{ background-color: #{"FF0000" if alert_level == "critical" else "FFA500"}; color: white; padding: 20px; }}
            .content {{ padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .critical {{ color: #FF0000; font-weight: bold; }}
            .high {{ color: #FF4500; font-weight: bold; }}
            .warning {{ color: #FFA500; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>⚠️ Budget Alert: {alert_level.upper()}</h1>
        </div>
        <div class="content">
            <h2>Platform Budget Status</h2>
            <ul>
                <li><strong>Spent:</strong> ${platform['spent_usd']:.2f} / ${platform['cap_usd']:.2f}</li>
                <li><strong>Utilization:</strong> {platform['utilization_percent']:.1f}%</li>
                <li><strong>Alert Level:</strong> <span class="{alert_level}">{alert_level}</span></li>
                <li><strong>Timestamp:</strong> {budget_status['timestamp']}</li>
            </ul>
    """
    
    if agents:
        html_body += f"""
            <h2>Agents Exceeding Thresholds ({len(agents)})</h2>
            <table>
                <tr>
                    <th>Agent ID</th>
                    <th>Spent</th>
                    <th>Cap</th>
                    <th>Utilization</th>
                    <th>Alert Level</th>
                </tr>
        """
        
        for agent in agents[:10]:  # Show top 10 agents
            html_body += f"""
                <tr>
                    <td><code>{agent['agent_id']}</code></td>
                    <td>${agent['spent_usd']:.2f}</td>
                    <td>${agent['cap_usd']:.2f}</td>
                    <td>{agent['utilization_percent']:.1f}%</td>
                    <td class="{agent['alert_level']}">{agent['alert_level']}</td>
                </tr>
            """
        
        html_body += "</table>"
        
        if len(agents) > 10:
            html_body += f"<p><em>... and {len(agents) - 10} more agents</em></p>"
    
    if alert_level == "critical":
        html_body += """
            <div style="background-color: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin-top: 20px;">
                <strong>🚨 Action Required:</strong> Platform budget at 100%. All agents will be auto-paused to prevent overspending.
            </div>
        """
    elif alert_level == "high":
        html_body += """
            <div style="background-color: #fff3e0; border-left: 4px solid #ff9800; padding: 15px; margin-top: 20px;">
                <strong>⚠️ Action Recommended:</strong> Platform budget at 95%. Consider pausing non-critical agents or increasing budget cap.
            </div>
        """
    
    html_body += """
        </div>
        <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #666;">
            WAOOAW Cost Guard | Automated Budget Monitoring
        </div>
    </body>
    </html>
    """
    
    # SendGrid API call
    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "personalizations": [
            {
                "to": [{"email": email.strip()} for email in ALERT_EMAIL_RECIPIENTS if email.strip()],
                "subject": f"⚠️ WAOOAW Budget Alert: {alert_level.upper()} - {platform['utilization_percent']:.1f}% Utilization"
            }
        ],
        "from": {"email": "alerts@waooaw.com", "name": "WAOOAW Cost Guard"},
        "content": [
            {"type": "text/html", "value": html_body}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers=headers,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        logger.info("Email alert sent successfully")
    except requests.RequestException as e:
        logger.error(f"Failed to send email alert: {e}")


def pause_all_agents() -> List[str]:
    """
    Auto-pause all agents when platform budget reaches 100%.
    
    Returns:
        List of agent IDs that were paused
    """
    if not PLANT_API_URL or not PLANT_API_KEY:
        logger.error("Plant API not configured, cannot pause agents")
        return []
    
    headers = {
        "Authorization": f"Bearer {PLANT_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Get list of active agents
        response = requests.get(
            f"{PLANT_API_URL}/api/v1/admin/agents?status=active",
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        agents = response.json().get("agents", [])
        
        paused_agents = []
        
        # Pause each agent
        for agent in agents:
            agent_id = agent["id"]
            try:
                pause_response = requests.post(
                    f"{PLANT_API_URL}/api/v1/admin/agents/{agent_id}/pause",
                    headers=headers,
                    json={
                        "reason": "budget_limit_exceeded",
                        "message": "Platform budget at 100%. Auto-paused by Cost Guard.",
                        "paused_by": "system"
                    },
                    timeout=10
                )
                pause_response.raise_for_status()
                paused_agents.append(agent_id)
                logger.info(f"Paused agent: {agent_id}")
            except requests.RequestException as e:
                logger.error(f"Failed to pause agent {agent_id}: {e}")
        
        return paused_agents
    
    except requests.RequestException as e:
        logger.error(f"Failed to get agent list: {e}")
        return []


def emit_metrics(budget_status: Dict) -> None:
    """
    Emit budget metrics to Google Cloud Monitoring.
    
    Args:
        budget_status: Budget status from get_budget_status()
    """
    try:
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{os.environ.get('GCP_PROJECT')}"
        
        now = datetime.now(timezone.utc)
        
        # Platform utilization metric
        series = monitoring_v3.TimeSeries()
        series.metric.type = "custom.googleapis.com/waooaw/budget/platform_utilization"
        series.resource.type = "global"
        
        point = monitoring_v3.Point()
        point.value.double_value = budget_status["platform"]["utilization_percent"]
        point.interval.end_time.seconds = int(now.timestamp())
        point.interval.end_time.nanos = now.microsecond * 1000
        
        series.points = [point]
        client.create_time_series(name=project_name, time_series=[series])
        
        # Alert level counter
        alert_level = budget_status["platform"]["alert_level"]
        series = monitoring_v3.TimeSeries()
        series.metric.type = f"custom.googleapis.com/waooaw/budget/alerts/{alert_level}"
        series.resource.type = "global"
        
        point = monitoring_v3.Point()
        point.value.int64_value = 1
        point.interval.end_time.seconds = int(now.timestamp())
        point.interval.end_time.nanos = now.microsecond * 1000
        
        series.points = [point]
        client.create_time_series(name=project_name, time_series=[series])
        
        logger.info("Metrics emitted to Cloud Monitoring")
    
    except Exception as e:
        logger.error(f"Failed to emit metrics: {e}")


@functions_framework.cloud_event
def handle_pubsub_event(cloud_event):
    """
    Handle Pub/Sub event from OPA decision logs.
    Triggered when OPA detects budget threshold breach.
    
    Event data structure:
    {
        "alert_level": "warning" | "high" | "critical",
        "platform_utilization": 87.5,
        "timestamp": "2026-01-17T12:34:56Z"
    }
    """
    import base64
    
    # Decode Pub/Sub message
    pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode()
    event_data = json.loads(pubsub_message)
    
    logger.info(f"Received budget alert event: {event_data}")
    
    # Get current budget status
    budget_status = get_budget_status()
    alert_level = budget_status["platform"]["alert_level"]
    
    # Send alerts based on level
    if alert_level in ["warning", "high", "critical"]:
        send_slack_alert(budget_status)
        send_email_alert(budget_status)
        emit_metrics(budget_status)
    
    # Auto-pause agents if critical
    if alert_level == "critical":
        paused_agents = pause_all_agents()
        logger.warning(f"Critical budget level: paused {len(paused_agents)} agents")
    
    return {"status": "processed", "alert_level": alert_level}


@functions_framework.http
def handle_http_request(request: Request):
    """
    Handle HTTP request for manual trigger or daily report.
    
    Query parameters:
    - action: "check" (default) | "report" | "pause"
    - force_alert: "true" | "false" (default)
    
    Examples:
    - GET /cost-guard?action=check
    - GET /cost-guard?action=report
    - POST /cost-guard?action=pause
    """
    action = request.args.get("action", "check")
    force_alert = request.args.get("force_alert", "false").lower() == "true"
    
    logger.info(f"HTTP request received: action={action}, force_alert={force_alert}")
    
    try:
        # Get current budget status
        budget_status = get_budget_status()
        alert_level = budget_status["platform"]["alert_level"]
        
        if action == "check":
            # Check budget and send alerts if needed
            if alert_level in ["warning", "high", "critical"] or force_alert:
                send_slack_alert(budget_status)
                send_email_alert(budget_status)
                emit_metrics(budget_status)
            
            if alert_level == "critical":
                paused_agents = pause_all_agents()
                budget_status["paused_agents"] = paused_agents
            
            return jsonify({
                "status": "ok",
                "budget_status": budget_status,
                "alert_sent": alert_level in ["warning", "high", "critical"] or force_alert
            })
        
        elif action == "report":
            # Generate daily budget report
            send_email_alert(budget_status)
            
            return jsonify({
                "status": "ok",
                "budget_status": budget_status,
                "report_sent": True
            })
        
        elif action == "pause":
            # Manual pause all agents
            if request.method != "POST":
                return jsonify({"error": "POST method required for pause action"}), 405
            
            paused_agents = pause_all_agents()
            
            return jsonify({
                "status": "ok",
                "paused_agents": paused_agents,
                "count": len(paused_agents)
            })
        
        else:
            return jsonify({"error": f"Unknown action: {action}"}), 400
    
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# For local testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode: print budget status
        status = get_budget_status()
        print(json.dumps(status, indent=2))
    else:
        # Run as Flask app for local development
        from flask import Flask
        app = Flask(__name__)
        app.add_url_rule("/", "cost_guard", handle_http_request, methods=["GET", "POST"])
        app.run(host="0.0.0.0", port=8080, debug=True)
