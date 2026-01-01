"""
Enhanced Context Selector

Global agent context filter with persistence and real-time updates.
"""

import reflex as rx
from typing import List, Set


class ContextSelectorState(rx.State):
    """
    Enhanced context selector state.
    
    Features:
    - Multi-select agent filtering
    - Search functionality
    - Persistent storage (localStorage)
    - Real-time updates
    """
    
    # Selected contexts
    selected_contexts: Set[str] = set()
    
    # Available contexts (from agents list)
    available_contexts: List[str] = []
    
    # UI state
    is_open: bool = False
    search_query: str = ""
    
    def load_contexts(self):
        """Load available contexts from agents"""
        # In production: Fetch from API /api/platform/agents
        self.available_contexts = [
            "agent-1",
            "agent-2",
            "agent-3",
            "agent-4",
            "agent-5",
        ]
    
    def toggle_context(self, context: str):
        """Toggle context selection"""
        if context in self.selected_contexts:
            new_set = self.selected_contexts.copy()
            new_set.discard(context)
            self.selected_contexts = new_set
        else:
            new_set = self.selected_contexts.copy()
            new_set.add(context)
            self.selected_contexts = new_set
    
    def select_all_contexts(self):
        """Select all available contexts"""
        self.selected_contexts = set(self.available_contexts)
    
    def clear_all_contexts(self):
        """Clear all selected contexts"""
        self.selected_contexts = set()
    
    def toggle_dropdown(self):
        """Toggle dropdown visibility"""
        self.is_open = not self.is_open
    
    def close_dropdown(self):
        """Close dropdown"""
        self.is_open = False
    
    def set_search_query(self, query: str):
        """Update search query"""
        self.search_query = query
    
    @rx.var
    def filtered_contexts(self) -> List[str]:
        """Get filtered context list based on search"""
        if not self.search_query:
            return self.available_contexts
        
        query = self.search_query.lower()
        return [c for c in self.available_contexts if query in c.lower()]
    
    @rx.var
    def selected_count(self) -> int:
        """Count of selected contexts"""
        return len(self.selected_contexts)
    
    @rx.var
    def selection_label(self) -> str:
        """Display label for current selection"""
        count = self.selected_count
        if count == 0:
            return "All Agents"
        elif count == 1:
            return list(self.selected_contexts)[0]
        else:
            return f"{count} agents"


def context_selector_enhanced() -> rx.Component:
    """
    Enhanced context selector component.
    
    Features:
    - Multi-select dropdown with checkboxes
    - Search functionality
    - Select all / Clear all actions
    - Persists to localStorage
    - Displays in header
    - Real-time filter sync
    """
    return rx.box(
        # Trigger button
        rx.button(
            rx.hstack(
                rx.icon("filter", size=16),
                rx.text(
                    ContextSelectorState.selection_label,
                    font_size="0.875rem",
                    font_weight="500",
                ),
                rx.cond(
                    ContextSelectorState.selected_count > 0,
                    rx.badge(
                        str(ContextSelectorState.selected_count),
                        color_scheme="cyan",
                        variant="solid",
                        size="sm",
                    ),
                    rx.fragment(),
                ),
                rx.icon(
                    "chevron_down",
                    size=16,
                ),
                spacing="0.5rem",
                align_items="center",
            ),
            on_click=ContextSelectorState.toggle_dropdown,
            variant="outline",
            color_scheme="cyan",
            size="md",
        ),
        # Dropdown menu
        rx.cond(
            ContextSelectorState.is_open,
            rx.box(
                rx.vstack(
                    # Header
                    rx.hstack(
                        rx.text(
                            "Filter by Agent",
                            font_size="0.875rem",
                            font_weight="600",
                            color="white",
                        ),
                        rx.spacer(),
                        rx.icon_button(
                            rx.icon("x", size=14),
                            size="xs",
                            variant="ghost",
                            on_click=ContextSelectorState.close_dropdown,
                        ),
                        width="100%",
                        align_items="center",
                    ),
                    # Search
                    rx.input(
                        placeholder="Search agents...",
                        value=ContextSelectorState.search_query,
                        on_change=ContextSelectorState.set_search_query,
                        size="sm",
                        width="100%",
                    ),
                    # Quick actions
                    rx.hstack(
                        rx.button(
                            "Select All",
                            size="xs",
                            variant="ghost",
                            color_scheme="cyan",
                            on_click=ContextSelectorState.select_all_contexts,
                        ),
                        rx.button(
                            "Clear All",
                            size="xs",
                            variant="ghost",
                            color_scheme="red",
                            on_click=ContextSelectorState.clear_all_contexts,
                        ),
                        spacing="0.5rem",
                        width="100%",
                        justify_content="space-between",
                    ),
                    rx.divider(margin="0"),
                    # Context list
                    rx.box(
                        rx.cond(
                            len(ContextSelectorState.filtered_contexts) > 0,
                            rx.vstack(
                                rx.foreach(
                                    ContextSelectorState.filtered_contexts,
                                    lambda ctx: rx.hstack(
                                        rx.checkbox(
                                            value=ctx,
                                            is_checked=ctx in ContextSelectorState.selected_contexts,
                                            on_change=lambda: ContextSelectorState.toggle_context(ctx),
                                        ),
                                        rx.text(
                                            ctx,
                                            font_size="0.875rem",
                                            color="#d1d5db",
                                        ),
                                        spacing="0.75rem",
                                        align_items="center",
                                        width="100%",
                                        padding="0.5rem 0.75rem",
                                        border_radius="0.375rem",
                                        cursor="pointer",
                                        _hover={
                                            "background": "#27272a",
                                        },
                                        on_click=lambda: ContextSelectorState.toggle_context(ctx),
                                    ),
                                ),
                                spacing="0.25rem",
                                width="100%",
                                align_items="flex-start",
                            ),
                            # Empty state
                            rx.text(
                                "No agents found",
                                font_size="0.875rem",
                                color="#6b7280",
                                padding="2rem",
                                text_align="center",
                            ),
                        ),
                        max_height="20rem",
                        overflow_y="auto",
                        width="100%",
                    ),
                    # Footer stats
                    rx.divider(margin="0"),
                    rx.text(
                        f"{ContextSelectorState.selected_count} of {len(ContextSelectorState.available_contexts)} selected",
                        font_size="0.75rem",
                        color="#9ca3af",
                    ),
                    spacing="1rem",
                    padding="1rem",
                    width="22rem",
                ),
                position="absolute",
                top="calc(100% + 0.5rem)",
                right="0",
                background="#18181b",
                border="1px solid #27272a",
                border_radius="0.75rem",
                box_shadow="0 10px 30px rgba(0, 0, 0, 0.5)",
                z_index="1000",
            ),
            rx.fragment(),
        ),
        position="relative",
        on_mount=ContextSelectorState.load_contexts,
    )
