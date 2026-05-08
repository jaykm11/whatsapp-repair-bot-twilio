#!/bin/bash
# WhatsApp Home Repair AI Agent - Startup Script

cd "$(dirname "$0")"
export PYTHONPATH=.
python app/main.py
