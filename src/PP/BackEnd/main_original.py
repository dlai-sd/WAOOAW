from main_proxy import app
from api import customers, billing, governor
from settings import APP_PORT
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(billing.router, prefix="/api/billing", tags=["billing"])

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
