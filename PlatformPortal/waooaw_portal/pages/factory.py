"""
Agent Factory Page

Wizard interface to create and deploy new agents from templates.
"""

import reflex as rx
from waooaw_portal.state.factory_state import FactoryState, AgentTemplate
from waooaw_portal.components.factory.wizard_stepper import wizard_stepper
from waooaw_portal.components.factory.template_card import template_card


def step1_template_selection() -> rx.Component:
    """Step 1: Choose Template"""
    return rx.vstack(
        rx.text(
            "Choose an Agent Template",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Select a pre-built template or start from scratch",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Template grid
        rx.box(
            rx.foreach(
                FactoryState.templates,
                lambda t: rx.box(
                    template_card(t, False),
                    on_click=lambda: FactoryState.select_template(t.template_id),
                ),
            ),
            display="grid",
            grid_template_columns="repeat(auto-fill, minmax(20rem, 1fr))",
            gap="1.5rem",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def step2_configure_agent() -> rx.Component:
    """Step 2: Configure Agent"""
    return rx.vstack(
        rx.text(
            "Configure Your Agent",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Set up agent properties and resources",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Configuration form
        rx.box(
            rx.vstack(
                # Basic Info
                rx.text("Basic Information", font_size="1.125rem", font_weight="600", color="white"),
                rx.input(
                    placeholder="Agent Name (e.g., my-memory-agent)",
                    value=FactoryState.agent_name,
                    on_change=FactoryState.update_agent_name,
                    width="100%",
                ),
                rx.text_area(
                    placeholder="Description (optional, max 200 chars)",
                    value=FactoryState.agent_description,
                    on_change=FactoryState.update_agent_description,
                    width="100%",
                    height="4rem",
                ),
                rx.select(
                    ["Starter", "Professional", "Enterprise"],
                    placeholder="Select Tier",
                    value=FactoryState.agent_tier,
                    on_change=FactoryState.update_agent_tier,
                    width="100%",
                ),
                # Capabilities
                rx.text("Capabilities", font_size="1.125rem", font_weight="600", color="white", margin_top="1.5rem"),
                rx.cond(
                    FactoryState.selected_template is not None,
                    rx.hstack(
                        rx.foreach(
                            FactoryState.selected_template.required_capabilities,
                            lambda cap: rx.badge(
                                cap,
                                color_scheme="cyan",
                                variant="solid",
                            ),
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    rx.text("No template selected", color="#9ca3af"),
                ),
                # Resources
                rx.text("Resources", font_size="1.125rem", font_weight="600", color="white", margin_top="1.5rem"),
                rx.grid(
                    rx.vstack(
                        rx.text("CPU Cores", font_size="0.875rem", color="#9ca3af"),
                        rx.select(
                            ["0.5", "1", "2", "4"],
                            value=str(FactoryState.cpu_cores),
                            width="100%",
                        ),
                        align_items="flex-start",
                    ),
                    rx.vstack(
                        rx.text("Memory (GB)", font_size="0.875rem", color="#9ca3af"),
                        rx.select(
                            ["1", "2", "4", "8"],
                            value=str(FactoryState.memory_gb),
                            width="100%",
                        ),
                        align_items="flex-start",
                    ),
                    rx.vstack(
                        rx.text("Storage (GB)", font_size="0.875rem", color="#9ca3af"),
                        rx.select(
                            ["1", "5", "10", "20"],
                            value=str(FactoryState.storage_gb),
                            width="100%",
                        ),
                        align_items="flex-start",
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                # Validation errors
                rx.cond(
                    len(FactoryState.validation_errors) > 0,
                    rx.vstack(
                        rx.foreach(
                            FactoryState.validation_errors,
                            lambda err: rx.text(
                                f"⚠️ {err}",
                                font_size="0.875rem",
                                color="#ef4444",
                            ),
                        ),
                        margin_top="1rem",
                        padding="1rem",
                        background="#ef444420",
                        border="1px solid #ef4444",
                        border_radius="0.5rem",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            padding="2rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def step3_sandbox_test() -> rx.Component:
    """Step 3: Test in Sandbox"""
    return rx.vstack(
        rx.text(
            "Test in Sandbox",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Run tests in an isolated environment",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Sandbox panel
        rx.box(
            rx.vstack(
                # Controls
                rx.hstack(
                    rx.button(
                        "Run Tests",
                        on_click=FactoryState.start_sandbox_test,
                        color_scheme="cyan",
                        is_disabled=FactoryState.sandbox_active,
                    ),
                    rx.badge(
                        FactoryState.sandbox_status.upper(),
                        color_scheme="green" if FactoryState.sandbox_status == "passed" else "gray",
                    ),
                    width="100%",
                    justify_content="space-between",
                ),
                # Logs
                rx.box(
                    rx.cond(
                        len(FactoryState.sandbox_logs) > 0,
                        rx.vstack(
                            rx.foreach(
                                FactoryState.sandbox_logs,
                                lambda log: rx.hstack(
                                    rx.text(
                                        log.timestamp,
                                        font_size="0.75rem",
                                        color="#6b7280",
                                        width="5rem",
                                    ),
                                    rx.text(
                                        log.message,
                                        font_size="0.875rem",
                                        color="#10b981" if log.level == "success" else "#ffffff",
                                    ),
                                    spacing="4",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        rx.text(
                            "Click 'Run Tests' to start sandbox testing",
                            font_size="0.875rem",
                            color="#9ca3af",
                            padding="2rem",
                            text_align="center",
                        ),
                    ),
                    padding="1rem",
                    background="#0a0a0a",
                    border="1px solid #27272a",
                    border_radius="0.5rem",
                    height="20rem",
                    overflow_y="auto",
                    margin_top="1rem",
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            padding="2rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def step4_provision() -> rx.Component:
    """Step 4: Provision Infrastructure"""
    return rx.vstack(
        rx.text(
            "Provision Infrastructure",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Automated infrastructure setup",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Info box
        rx.box(
            rx.vstack(
                rx.text(
                    "Infrastructure will be automatically provisioned:",
                    font_size="1rem",
                    font_weight="600",
                    color="white",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.icon("check", color="#10b981"),
                        rx.text("Docker container creation", color="#9ca3af"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.icon("check", color="#10b981"),
                        rx.text("Message queue setup", color="#9ca3af"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.icon("check", color="#10b981"),
                        rx.text("Storage allocation", color="#9ca3af"),
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.icon("check", color="#10b981"),
                        rx.text("Monitoring configuration", color="#9ca3af"),
                        spacing="2",
                    ),
                    align_items="flex-start",
                    spacing="0.75rem",
                    margin_top="1rem",
                ),
                rx.text(
                    "This process is fully automated and will take approximately 2-3 minutes.",
                    font_size="0.875rem",
                    color="#6b7280",
                    margin_top="1.5rem",
                ),
                align_items="flex-start",
                spacing="2",
                width="100%",
            ),
            padding="2rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            width="100%",
        ),
        spacing="4",
        width="100%",
    )


def step5_review_deploy() -> rx.Component:
    """Step 5: Review & Deploy"""
    return rx.vstack(
        rx.text(
            "Review & Deploy",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Final review before deployment",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Review sections
        rx.grid(
            # Configuration summary
            rx.box(
                rx.vstack(
                    rx.text("Configuration", font_size="1.125rem", font_weight="600", color="white"),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Name:", font_weight="600", color="#9ca3af"),
                            rx.text(FactoryState.agent_name, color="white"),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.text("Template:", font_weight="600", color="#9ca3af"),
                            rx.text(
                                FactoryState.selected_template.name if FactoryState.selected_template else "N/A",
                                color="white",
                            ),
                            spacing="2",
                        ),
                        rx.hstack(
                            rx.text("Tier:", font_weight="600", color="#9ca3af"),
                            rx.text(FactoryState.agent_tier, color="white"),
                            spacing="2",
                        ),
                        align_items="flex-start",
                        spacing="2",
                    ),
                    align_items="flex-start",
                    spacing="4",
                    width="100%",
                ),
                padding="1.5rem",
                background="#18181b",
                border="1px solid #27272a",
                border_radius="1rem",
            ),
            # Cost estimate
            rx.box(
                rx.vstack(
                    rx.text("Cost Estimate", font_size="1.125rem", font_weight="600", color="white"),
                    rx.vstack(
                        rx.text(
                            f"${FactoryState.estimated_monthly_cost:.2f}/month",
                            font_size="2rem",
                            font_weight="700",
                            color="#00f2fe",
                        ),
                        rx.vstack(
                            rx.foreach(
                                FactoryState.cost_breakdown.items(),
                                lambda item: rx.hstack(
                                    rx.text(item[0], font_size="0.875rem", color="#9ca3af"),
                                    rx.text(f"${item[1]:.2f}", font_size="0.875rem", color="white"),
                                    width="100%",
                                    justify_content="space-between",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        align_items="flex-start",
                        spacing="4",
                        width="100%",
                    ),
                    align_items="flex-start",
                    spacing="4",
                    width="100%",
                ),
                padding="1.5rem",
                background="#18181b",
                border="1px solid #27272a",
                border_radius="1rem",
            ),
            columns="2",
            spacing="6",
            width="100%",
        ),
        # Deploy button
        rx.button(
            "Deploy Agent",
            on_click=lambda: [FactoryState.calculate_cost_estimate(), FactoryState.deploy_agent(), FactoryState.next_step()],
            size="4",
            color_scheme="cyan",
            width="100%",
            margin_top="2rem",
        ),
        spacing="4",
        width="100%",
    )


def step6_monitor_deployment() -> rx.Component:
    """Step 6: Monitor Deployment"""
    return rx.vstack(
        rx.text(
            "Deployment in Progress",
            font_size="1.5rem",
            font_weight="700",
            color="white",
        ),
        rx.text(
            "Your agent is being deployed",
            font_size="1rem",
            color="#9ca3af",
            margin_bottom="2rem",
        ),
        # Progress
        rx.box(
            rx.vstack(
                # Progress bar
                rx.vstack(
                    rx.hstack(
                        rx.text("Progress", font_size="1rem", font_weight="600", color="white"),
                        rx.text(f"{FactoryState.deployment_progress}%", font_size="1rem", color="#00f2fe"),
                        width="100%",
                        justify_content="space-between",
                    ),
                    rx.box(
                        rx.box(
                            width=f"{FactoryState.deployment_progress}%",
                            height="100%",
                            background="#00f2fe",
                            border_radius="0.25rem",
                            transition="width 0.3s ease",
                        ),
                        width="100%",
                        height="0.5rem",
                        background="#27272a",
                        border_radius="0.25rem",
                    ),
                    spacing="2",
                    width="100%",
                ),
                # Deployment steps
                rx.vstack(
                    rx.foreach(
                        FactoryState.deployment_steps,
                        lambda step: rx.hstack(
                            rx.cond(
                                step.status == "completed",
                                rx.icon("check-circle", color="#10b981", size=20),
                                rx.cond(
                                    step.status == "running",
                                    rx.spinner(size="2", color="#00f2fe"),
                                    rx.icon("circle", color="#6b7280", size=20),
                                ),
                            ),
                            rx.vstack(
                                rx.text(step.step_name, font_size="0.875rem", font_weight="600", color="white"),
                                rx.text(step.message, font_size="0.75rem", color="#9ca3af"),
                                align_items="flex-start",
                                spacing="0.25rem",
                            ),
                            spacing="4",
                            align_items="flex-start",
                        ),
                    ),
                    spacing="4",
                    margin_top="2rem",
                    width="100%",
                ),
                # Success message
                rx.cond(
                    FactoryState.deployment_status == "success",
                    rx.box(
                        rx.vstack(
                            rx.icon("check-circle", color="#10b981", size=40),
                            rx.text(
                                "Agent Deployed Successfully! 🎉",
                                font_size="1.25rem",
                                font_weight="700",
                                color="#10b981",
                            ),
                            rx.text(
                                f"Agent ID: {FactoryState.deployed_agent_id}",
                                font_size="0.875rem",
                                color="#9ca3af",
                            ),
                            rx.hstack(
                                rx.button(
                                    "View Agent Dashboard",
                                    href="/agents",
                                    color_scheme="cyan",
                                ),
                                rx.button(
                                    "Create Another Agent",
                                    on_click=FactoryState.reset_wizard,
                                    variant="outline",
                                    color_scheme="gray",
                                ),
                                spacing="4",
                                margin_top="1rem",
                            ),
                            spacing="4",
                            align_items="center",
                        ),
                        padding="2rem",
                        background="#10b98120",
                        border="1px solid #10b981",
                        border_radius="1rem",
                        margin_top="2rem",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="4",
                width="100%",
            ),
            padding="2rem",
            background="#18181b",
            border="1px solid #27272a",
            border_radius="1rem",
            width="100%",
        ),
        # Auto-complete for demo
        rx.button(
            "Complete Deployment (Demo)",
            on_click=FactoryState.complete_deployment,
            size="2",
            variant="ghost",
            color_scheme="gray",
            margin_top="1rem",
        ),
        spacing="4",
        width="100%",
    )


def factory_page() -> rx.Component:
    """
    Agent Factory page - Wizard to create and deploy new agents.
    
    Features:
    - 6-step wizard interface
    - Template selection
    - Configuration form
    - Sandbox testing
    - Cost estimation
    - Real-time deployment monitoring
    """
    return rx.box(
        rx.vstack(
            # Header
            rx.text(
                "Agent Factory",
                font_size="2rem",
                font_weight="700",
                color="white",
            ),
            # Wizard stepper
            wizard_stepper(FactoryState.current_step, FactoryState.step_titles),
            # Step content
            rx.box(
                rx.match(
                    FactoryState.current_step,
                    (0, step1_template_selection()),
                    (1, step2_configure_agent()),
                    (2, step3_sandbox_test()),
                    (3, step4_provision()),
                    (4, step5_review_deploy()),
                    (5, step6_monitor_deployment()),
                    step1_template_selection(),  # Default
                ),
                width="100%",
            ),
            # Navigation buttons
            rx.cond(
                FactoryState.current_step < 5,
                rx.hstack(
                    rx.button(
                        "Back",
                        on_click=FactoryState.previous_step,
                        variant="outline",
                        color_scheme="gray",
                        is_disabled=FactoryState.current_step == 0,
                    ),
                    rx.button(
                        "Next",
                        on_click=FactoryState.next_step,
                        color_scheme="cyan",
                        is_disabled=~FactoryState.can_proceed,
                    ),
                    width="100%",
                    justify_content="space-between",
                    margin_top="2rem",
                ),
                rx.fragment(),
            ),
            spacing="8",
            width="100%",
            max_width="90rem",
            margin="0 auto",
            padding="2rem",
        ),
        width="100%",
        min_height="100vh",
        background="#0a0a0a",
        on_mount=FactoryState.load_templates,
    )
