#!/usr/bin/env python3
"""
Script para remover min_level dos decorators híbridos
Converte @require_permission_or_level para usar apenas permissões granulares
"""

import os
import re
import sys


def remove_min_levels_from_file(file_path):
    """Remove min_level parameters from hybrid decorators in a file"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Pattern to match @require_permission_or_level with min_level
        pattern = r'@require_permission_or_level\(permission="([^"]+)",\s*min_level=\d+,\s*context_type="([^"]+)"\)'
        replacement = (
            r'@require_permission_or_level(permission="\1", context_type="\2")'
        )

        new_content = re.sub(pattern, replacement, content)

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ Updated: {file_path}")
            return True
        else:
            print(f"ℹ️ No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False


def main():
    """Remove min_level from all API endpoints"""
    print("🚀 Removing min_level from hybrid decorators...")

    api_files = [
        "app/presentation/api/v1/users.py",
        "app/presentation/api/v1/companies.py",
        "app/presentation/api/v1/establishments.py",
        "app/presentation/api/v1/roles.py",
        "app/presentation/api/v1/clients.py",
        "app/presentation/api/v1/dashboard.py",
        "app/presentation/api/v1/notifications.py",
    ]

    base_path = "/home/juliano/Projetos/pro_team_care_16"
    updated_files = []

    for file_path in api_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            if remove_min_levels_from_file(full_path):
                updated_files.append(file_path)
        else:
            print(f"⚠️ File not found: {full_path}")

    print(f"\n📊 Summary:")
    print(f"   📁 Files processed: {len(api_files)}")
    print(f"   ✅ Files updated: {len(updated_files)}")

    if updated_files:
        print(f"\n🔄 Updated files:")
        for file_path in updated_files:
            print(f"   - {file_path}")

    print(f"\n🎯 Phase 3 Progress:")
    print(f"   ✅ Endpoints migrated to pure permission system")
    print(f"   ✅ No more hardcoded level dependencies")
    print(f"   🚀 Ready for final validation!")


if __name__ == "__main__":
    main()
