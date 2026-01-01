import reflex as rx

config = rx.Config(
    app_name="waooaw_portal",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)