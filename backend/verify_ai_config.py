#!/usr/bin/env python3
"""
Quick verification that AI model configuration is properly loaded from .env
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(override=True)

from config import settings

print("\n" + "=" * 60)
print("🔍 AI Model Configuration Verification")
print("=" * 60)

print("\n📋 Models loaded from .env:")
print(f"   PRIMARY:   {settings.openrouter_primary_model}")
print(f"   SECONDARY: {settings.openrouter_secondary_model}")
print(f"   TERTIARY:  {settings.openrouter_tertiary_model}")
print(f"   BACKUP:    {settings.openrouter_backup_model}")

print(f"\n🌡️  Temperature: {settings.openrouter_temperature}")
print(f"🔑 API Key: {'✅ Configured' if settings.openrouter_api_key else '❌ Missing'}")

# Verify expected values (COST OPTIMIZED 2025-12-01)
expected = {
    "primary": "x-ai/grok-4.1-fast:free",
    "secondary": "x-ai/grok-4-fast",
    "tertiary": "openai/gpt-oss-120b",
    "backup": "google/gemini-2.5-flash-lite"
}

print("\n✅ Configuration Check:")
all_correct = True
if settings.openrouter_primary_model == expected["primary"]:
    print(f"   ✅ Primary model correct")
else:
    print(f"   ❌ Primary model mismatch: expected {expected['primary']}")
    all_correct = False

if settings.openrouter_secondary_model == expected["secondary"]:
    print(f"   ✅ Secondary model correct")
else:
    print(f"   ❌ Secondary model mismatch: expected {expected['secondary']}")
    all_correct = False

if settings.openrouter_tertiary_model == expected["tertiary"]:
    print(f"   ✅ Tertiary model correct")
else:
    print(f"   ❌ Tertiary model mismatch: expected {expected['tertiary']}")
    all_correct = False

if settings.openrouter_backup_model == expected["backup"]:
    print(f"   ✅ Backup model correct")
else:
    print(f"   ❌ Backup model mismatch: expected {expected['backup']}")
    all_correct = False

if all_correct:
    print("\n🎉 All AI model configurations are correct!")
else:
    print("\n⚠️  Some configurations need attention. Check .env file.")

print("\n" + "=" * 60)
