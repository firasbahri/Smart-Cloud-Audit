import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from mongoDB import MongoDB
from rabbitMq.connection import RabbitMQConnection
MongoDB.connect()

from api.auth import router as auth_router
from api.cloudAuth import router as cloud_auth_router
from api.cloud_scan import router as cloud_scan_router


print("inicio de applicacion...")

app = FastAPI()


#@app.on_event("startup")
#async def startup_event():
 #   await RabbitMQConnection.connect()




app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth_router, prefix="/auth")
app.include_router(cloud_auth_router, prefix="/cloud")
app.include_router(cloud_scan_router)