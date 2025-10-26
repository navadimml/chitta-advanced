#!/bin/bash
cd /home/user/chitta-advanced/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
