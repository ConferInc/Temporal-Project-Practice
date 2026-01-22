import os
from temporalio.client import Client
from app.core import config

async def get_client():
    return await Client.connect(config.TEMPORAL_HOST)
