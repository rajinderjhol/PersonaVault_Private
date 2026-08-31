import re

# Read App.tsx
with open('studio/src/App.tsx', 'r') as f:
    app_content = f.read()

# Extract routes from App.tsx
routes_in_app = re.findall(r'<Route path="([^"]+)"', app_content)

# Read navigation-tabs.md
with open('docs/temp/navigation-tabs.md', 'r') as f:
    nav_content = f.read()

# Extract routes from nav tabs (a bit naive but should work for this structure)
# Looking for lines like | Name | /route | ...
routes_in_nav = []
for line in nav_content.split('\n'):
    if '|' in line and '/' in line:
        parts = line.split('|')
        if len(parts) > 2:
            route = parts[2].strip().replace('`', '')
            if route.startswith('/'):
                routes_in_nav.append(route)

print(f"Routes in App.tsx: {sorted(routes_in_app)}")
print(f"Routes in nav-tabs.md: {sorted(routes_in_nav)}")

missing_in_nav = set(routes_in_app) - set(routes_in_nav)
missing_in_app = set(routes_in_nav) - set(routes_in_app)

print(f"\nMissing in nav: {missing_in_app}")
print(f"Missing in app: {missing_in_app}")
