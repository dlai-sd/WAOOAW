"""
Agent Servicing Page - Story 5.1.11
Zero-downtime agent upgrades with automatic rollback
"""

import reflex as rx
from ..state.servicing_state import ServicingState
from ..components.servicing import wizard_stepper, strategy_selector, deployment_monitor, health_monitor, config_editor


def step1_plan() -> rx.Component:
    """Step 1: Plan upgrade - Select agents and target version"""
    return rx.vstack(
        rx.heading("Plan Upgrade", size="7", weight="bold"),
        rx.text("Select agents and target version for upgrade", color="gray"),
        
        # Agent selection
        rx.vstack(
            rx.heading("Available Agents", size="5", weight="bold", margin_top="1.5rem"),
            rx.text("Review agents available for upgrade", color="gray"),
            
            rx.vstack(
                rx.foreach(
                    ServicingState.agents,
                    lambda agent: rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text(agent.name, weight="bold", font_size="1.1rem"),
                                rx.badge(agent.category, color_scheme="blue"),
                                rx.badge(
                                    agent.health,
                                    color_scheme=rx.cond(
                                        agent.health == "healthy",
                                        "green",
                                        rx.cond(
                                            agent.health == "degraded",
                                            "yellow",
                                            "gray"
                                        )
                                    ),
                                ),
                            ),
                            rx.hstack(
                                rx.text(f"Version: {agent.current_version}", color="gray", font_size="0.9rem"),
                                rx.text(f"Status: {agent.status}", color="gray", font_size="0.9rem"),
                                rx.text(f"Uptime: {agent.uptime_days}d", color="gray", font_size="0.9rem"),
                            ),
                            align_items="start",
                            spacing="2",
                            width="100%",
                        ),
                        padding="1rem",
                        margin_bottom="0.5rem",
                    ),
                ),
                width="100%",
                spacing="2",
            ),
            width="100%",
            align_items="start",
        ),
        
        # Version selection
        rx.vstack(
            rx.heading("Target Version", size="5", weight="bold", margin_top="1.5rem"),
            rx.grid(
                rx.foreach(
                    ServicingState.available_versions,
                    lambda version: rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text(version.version, weight="bold", font_size="1.2rem"),
                                rx.cond(
                                    version.is_current,
                                    rx.badge("CURRENT", color_scheme="green"),
                                    rx.cond(
                                        version.is_recommended,
                                        rx.badge("RECOMMENDED", color_scheme="cyan"),
                                        rx.fragment(),
                                    ),
                                ),
                                rx.cond(
                                    version.status == "deprecated",
                                    rx.badge("DEPRECATED", color_scheme="red"),
                                    rx.fragment(),
                                ),
                            ),
                            rx.text(f"Released: {version.release_date}", color="gray", font_size="0.85rem"),
                            rx.text(version.changelog, color="gray", font_size="0.9rem", margin_top="0.5rem"),
                            rx.text(f"Size: {version.size_mb} MB", color="gray", font_size="0.85rem", margin_top="0.5rem"),
                            rx.button(
                                "Select Version",
                                on_click=ServicingState.select_version(version.version_id),
                                color_scheme=rx.cond(
                                    ServicingState.selected_version == version.version_id,
                                    "cyan",
                                    "gray",
                                ),
                                margin_top="1rem",
                                width="100%",
                            ),
                            align_items="start",
                            spacing="2",
                        ),
                        padding="1rem",
                    ),
                ),
                columns="2",
                spacing="4",
                width="100%",
            ),
            width="100%",
            align_items="start",
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def step2_backup() -> rx.Component:
    """Step 2: Backup current state"""
    return rx.vstack(
        rx.heading("Backup Configuration", size="7", weight="bold"),
        rx.text("Create backup for safe rollback", color="gray"),
        
        rx.vstack(
            rx.card(
                rx.vstack(
                    rx.heading("Backup Settings", size="5", weight="bold"),
                    
                    rx.hstack(
                        rx.text("Backup Enabled:", weight="bold"),
                        rx.switch(
                            checked=ServicingState.backup_enabled,
                            on_change=ServicingState.set_backup_enabled,
                        ),
                    ),
                    
                    rx.vstack(
                        rx.text("Backup Location:", weight="bold"),
                        rx.input(
                            value=ServicingState.backup_location,
                            on_change=ServicingState.set_backup_location,
                            width="100%",
                        ),
                        align_items="start",
                        width="100%",
                    ),
                    
                    rx.divider(margin="1rem 0"),
                    
                    rx.cond(
                        ServicingState.backup_status == "pending",
                        rx.button(
                            "Create Backup",
                            on_click=ServicingState.create_backup,
                            color_scheme="cyan",
                            size="3",
                        ),
                        rx.cond(
                            ServicingState.backup_status == "in_progress",
                            rx.hstack(
                                rx.spinner(),
                                rx.text("Creating backup...", color="cyan"),
                            ),
                            rx.hstack(
                                rx.icon("check-circle", color="green", size=24),
                                rx.text("Backup completed successfully", color="green", weight="bold"),
                            ),
                        ),
                    ),
                    
                    rx.cond(
                        ServicingState.backup_status == "completed",
                        rx.vstack(
                            rx.text("Backup Details:", weight="bold", margin_top="1rem"),
                            rx.text(f"Location: {ServicingState.backup_location}", color="gray", font_size="0.9rem"),
                            rx.text(f"Agents: {ServicingState.selected_agent_count}", color="gray", font_size="0.9rem"),
                            rx.text("Timestamp: (backup timestamp)", color="gray", font_size="0.9rem"),
                            align_items="start",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    
                    align_items="start",
                    spacing="4",
                    width="100%",
                ),
                padding="1.5rem",
                width="100%",
            ),
            
            rx.callout.root(
                rx.callout.icon(rx.icon("info", size=20)),
                rx.callout.text("Backups enable instant rollback if the upgrade encounters issues."),
                color_scheme="blue",
                margin_top="1rem",
                width="100%",
            ),
            
            width="100%",
            align_items="start",
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def step3_deploy() -> rx.Component:
    """Step 3: Deploy new version with strategy selection"""
    return rx.vstack(
        rx.heading("Deployment Strategy", size="7", weight="bold"),
        rx.text("Select deployment approach for zero-downtime upgrade", color="gray"),
        
        strategy_selector(),
        
        rx.cond(
            ServicingState.selected_strategy != None,
            rx.vstack(
                rx.heading("Strategy Configuration", size="5", weight="bold", margin_top="1.5rem"),
                
                # Blue-Green specific config
                rx.cond(
                    ServicingState.selected_strategy == "blue-green",
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Validation Period:", weight="bold"),
                                rx.input(
                                    value=ServicingState.validation_period_sec,
                                    type="number",
                                    on_change=lambda v: ServicingState.update_strategy_config("validation_period_sec", v),
                                    width="100px",
                                ),
                                rx.text("seconds"),
                            ),
                            rx.hstack(
                                rx.text("Keep Old Version:", weight="bold"),
                                rx.switch(
                                    checked=ServicingState.keep_old_version,
                                    on_change=lambda v: ServicingState.update_strategy_config("keep_old_version", v),
                                ),
                            ),
                            align_items="start",
                            spacing="4",
                        ),
                        padding="1rem",
                    ),
                    rx.fragment(),
                ),
                
                # Canary specific config
                rx.cond(
                    ServicingState.selected_strategy == "canary",
                    rx.card(
                        rx.vstack(
                            rx.text("Traffic Rollout Plan:", weight="bold"),
                            rx.hstack(
                                rx.text("Phase 1:"),
                                rx.input(
                                    value=ServicingState.phase1_traffic,
                                    type="number",
                                    width="80px",
                                ),
                                rx.text("%"),
                            ),
                            rx.hstack(
                                rx.text("Phase 2:"),
                                rx.input(
                                    value=ServicingState.phase2_traffic,
                                    type="number",
                                    width="80px",
                                ),
                                rx.text("%"),
                            ),
                            rx.hstack(
                                rx.text("Phase 3:"),
                                rx.input(
                                    value=ServicingState.phase3_traffic,
                                    type="number",
                                    width="80px",
                                ),
                                rx.text("%"),
                            ),
                            rx.hstack(
                                rx.text("Phase Duration:", weight="bold"),
                                rx.input(
                                    value=ServicingState.phase_duration_min,
                                    type="number",
                                    width="80px",
                                ),
                                rx.text("minutes"),
                            ),
                            align_items="start",
                            spacing="4",
                        ),
                        padding="1rem",
                    ),
                    rx.fragment(),
                ),
                
                # Rolling specific config
                rx.cond(
                    ServicingState.selected_strategy == "rolling",
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.text("Batch Size:", weight="bold"),
                                rx.input(
                                    value=ServicingState.batch_size,
                                    type="number",
                                    width="80px",
                                ),
                                rx.text("instances at a time"),
                            ),
                            rx.hstack(
                                rx.text("Wait Between Batches:", weight="bold"),
                                rx.input(
                                    value=ServicingState.wait_between_batches_sec,
                                    type="number",
                                    width="100px",
                                ),
                                rx.text("seconds"),
                            ),
                            align_items="start",
                            spacing="4",
                        ),
                        padding="1rem",
                    ),
                    rx.fragment(),
                ),
                
                width="100%",
                align_items="start",
            ),
            rx.fragment(),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def step4_test() -> rx.Component:
    """Step 4: Test new version with health checks"""
    return rx.vstack(
        rx.heading("Pre-Upgrade Testing", size="7", weight="bold"),
        rx.text("Validate environment health before upgrade", color="gray"),
        
        health_monitor(),
        
        rx.hstack(
            rx.text("Automatic Rollback:", weight="bold"),
            rx.switch(
                checked=ServicingState.auto_rollback_enabled,
                on_change=ServicingState.set_auto_rollback_enabled,
            ),
            rx.text("Automatically rollback if health checks fail", color="gray", font_size="0.9rem"),
            margin_top="1rem",
        ),
        
        rx.callout.root(
            rx.callout.icon(rx.icon("alert-triangle", size=20)),
            rx.callout.text("Automatic rollback triggers: Health check failure, Error rate >5%, Latency increase >50%"),
            color_scheme="orange",
            margin_top="1rem",
            width="100%",
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def step5_cutover() -> rx.Component:
    """Step 5: Execute upgrade with monitoring"""
    return rx.vstack(
        rx.heading("Upgrade Execution", size="7", weight="bold"),
        rx.text("Zero-downtime deployment in progress", color="gray"),
        
        deployment_monitor(),
        
        rx.cond(
            ServicingState.can_rollback & ~ServicingState.rollback_in_progress,
            rx.button(
                "🔄 Trigger Manual Rollback",
                on_click=ServicingState.trigger_rollback,
                color_scheme="red",
                variant="outline",
                margin_top="1rem",
            ),
            rx.fragment(),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def step6_verify() -> rx.Component:
    """Step 6: Post-upgrade verification"""
    return rx.vstack(
        rx.heading(
            rx.cond(
                ServicingState.upgrade_success,
                "Upgrade Completed Successfully ✅",
                "Upgrade Failed - Rolled Back 🔄",
            ),
            size="7",
            weight="bold",
        ),
        
        rx.cond(
            ServicingState.upgrade_success,
            rx.vstack(
                rx.text("All agents successfully upgraded with zero downtime", color="green", font_size="1.1rem"),
                
                rx.card(
                    rx.vstack(
                        rx.heading("Upgrade Summary", size="5", weight="bold"),
                        rx.hstack(
                            rx.text("Agents Upgraded:", weight="bold"),
                            rx.text(ServicingState.selected_agent_count),
                        ),
                        rx.hstack(
                            rx.text("Target Version:", weight="bold"),
                            rx.text(ServicingState.selected_version),
                        ),
                        rx.hstack(
                            rx.text("Strategy:", weight="bold"),
                            rx.text(ServicingState.selected_strategy),
                        ),
                        rx.hstack(
                            rx.text("Duration:", weight="bold"),
                            rx.text("~9 minutes"),
                        ),
                        rx.hstack(
                            rx.text("Downtime:", weight="bold"),
                            rx.text("0 seconds", color="green", weight="bold"),
                        ),
                        align_items="start",
                        spacing="4",
                    ),
                    padding="1.5rem",
                    margin_top="1rem",
                ),
                
                rx.hstack(
                    rx.button(
                        "View Agents",
                        on_click=rx.redirect("/agents"),
                        color_scheme="cyan",
                        size="3",
                    ),
                    rx.button(
                        "Upgrade More Agents",
                        on_click=ServicingState.reset_wizard,
                        variant="outline",
                        size="3",
                    ),
                    rx.button(
                        "View History",
                        on_click=rx.redirect("/servicing"),
                        variant="ghost",
                        size="3",
                    ),
                    spacing="4",
                    margin_top="1.5rem",
                ),
                
                width="100%",
                align_items="start",
            ),
            rx.vstack(
                rx.text("Upgrade encountered issues and was automatically rolled back", color="red", font_size="1.1rem"),
                
                rx.card(
                    rx.vstack(
                        rx.heading("Rollback Details", size="5", weight="bold"),
                        rx.text("All agents reverted to previous stable version", color="gray"),
                        rx.hstack(
                            rx.text("Rollback Time:", weight="bold"),
                            rx.text("<30 seconds", color="green", weight="bold"),
                        ),
                        rx.hstack(
                            rx.text("Data Loss:", weight="bold"),
                            rx.text("None", color="green", weight="bold"),
                        ),
                        align_items="start",
                        spacing="4",
                    ),
                    padding="1.5rem",
                    margin_top="1rem",
                ),
                
                rx.button(
                    "Try Again",
                    on_click=ServicingState.reset_wizard,
                    color_scheme="cyan",
                    size="3",
                    margin_top="1.5rem",
                ),
                
                width="100%",
                align_items="start",
            ),
        ),
        
        width="100%",
        align_items="start",
        spacing="4",
    )


def servicing_page() -> rx.Component:
    """Main servicing page with upgrade wizard"""
    return rx.container(
        rx.vstack(
            # Header
            rx.hstack(
                rx.heading("Agent Servicing", size="8", weight="bold"),
                rx.badge("Zero Downtime", color_scheme="green", font_size="1rem"),
                justify="between",
                align_items="center",
                width="100%",
                margin_bottom="1rem",
            ),
            
            # Wizard stepper
            wizard_stepper(ServicingState.current_step),
            
            rx.divider(margin="1.5rem 0"),
            
            # Step content
            rx.box(
                rx.cond(
                    ServicingState.current_step == 0,
                    step1_plan(),
                    rx.cond(
                        ServicingState.current_step == 1,
                        step2_backup(),
                        rx.cond(
                            ServicingState.current_step == 2,
                            step3_deploy(),
                            rx.cond(
                                ServicingState.current_step == 3,
                                step4_test(),
                                rx.cond(
                                    ServicingState.current_step == 4,
                                    step5_cutover(),
                                    step6_verify(),
                                ),
                            ),
                        ),
                    ),
                ),
                width="100%",
                min_height="400px",
            ),
            
            # Navigation buttons
            rx.cond(
                ServicingState.current_step < 5,
                rx.hstack(
                    rx.button(
                        "← Back",
                        on_click=ServicingState.previous_step,
                        variant="outline",
                        size="3",
                        disabled=ServicingState.current_step == 0,
                    ),
                    rx.cond(
                        ServicingState.current_step == 4,
                        rx.button(
                            "Start Upgrade →",
                            on_click=ServicingState.start_upgrade,
                            color_scheme="cyan",
                            size="3",
                            disabled=~ServicingState.can_proceed | ServicingState.is_upgrading,
                        ),
                        rx.button(
                            "Next →",
                            on_click=ServicingState.next_step,
                            color_scheme="cyan",
                            size="3",
                            disabled=~ServicingState.can_proceed,
                        ),
                    ),
                    justify="between",
                    width="100%",
                    margin_top="2rem",
                ),
                rx.fragment(),
            ),
            
            # Upgrade history
            rx.cond(
                ServicingState.current_step == 0,
                rx.vstack(
                    rx.divider(margin="2rem 0"),
                    rx.heading("Recent Upgrades", size="6", weight="bold"),
                    rx.table.root(
                        rx.table.header(
                            rx.table.row(
                                rx.table.column_header_cell("Agent"),
                                rx.table.column_header_cell("Upgrade"),
                                rx.table.column_header_cell("Strategy"),
                                rx.table.column_header_cell("Duration"),
                                rx.table.column_header_cell("Status"),
                                rx.table.column_header_cell("Date"),
                            ),
                        ),
                        rx.table.body(
                            rx.foreach(
                                ServicingState.upgrade_history,
                                lambda history: rx.table.row(
                                    rx.table.cell(history.agent_name),
                                    rx.table.cell(f"{history.from_version} → {history.to_version}"),
                                    rx.table.cell(history.strategy),
                                    rx.table.cell(f"{history.duration_min} min"),
                                    rx.table.cell(
                                        rx.badge(
                                            history.status,
                                            color_scheme=rx.cond(
                                                history.status == "completed",
                                                "green",
                                                rx.cond(
                                                    history.status == "failed",
                                                    "red",
                                                    "yellow",
                                                ),
                                            ),
                                        ),
                                    ),
                                    rx.table.cell(history.start_time),
                                ),
                            ),
                        ),
                        width="100%",
                    ),
                    width="100%",
                    align_items="start",
                    margin_top="2rem",
                ),
                rx.fragment(),
            ),
            
            width="100%",
            spacing="4",
        ),
        padding="2rem",
        max_width="1400px",
        on_mount=lambda: [
            ServicingState.load_agents(),
            ServicingState.load_versions(),
            ServicingState.load_strategies(),
            ServicingState.load_history(),
        ],
    )
