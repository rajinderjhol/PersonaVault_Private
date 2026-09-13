from app.main import app
from collections import Counter
import sys

def audit_routes():
    print("--- API Surface Audit ---")
    routes = []
    
    # Extract paths and tags
    for r in app.routes:
        if hasattr(r, "path"):
            routes.append(r.path)
            if hasattr(r, "tags"):
                print(f"Path: {r.path}, Tags: {r.tags}")
        elif hasattr(r, "routes"): # APIRouter
            for sub_r in r.routes:
                if hasattr(sub_r, "path"):
                    routes.append(sub_r.path)
                    if hasattr(sub_r, "tags"):
                        print(f"Path: {sub_r.path}, Tags: {sub_r.tags}")

    # Check for duplicates
    dupes = {p: n for p, n in Counter(routes).items() if n > 1}
    if dupes:
        print("\n❌ Duplicate routes found:")
        for p, n in sorted(dupes.items()):
            print(f"  {n}x {p}")
    else:
        print("\n✅ No duplicate routes.")

    # Check for double-prefix
    double_prefix = [p for p in routes if "/api/v1/api/v1" in p]
    if double_prefix:
        print("\n❌ Double-prefix routes found:")
        for p in double_prefix:
            print(f"  {p}")
    else:
        print("\n✅ No double-prefix routes.")

if __name__ == "__main__":
    audit_routes()
