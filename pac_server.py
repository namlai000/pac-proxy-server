from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
from urllib.parse import urlparse

# ──────────────────────────────────────────────
# Configuration — edit these values as needed
# ──────────────────────────────────────────────
PAC_SERVER_PORT = int(os.environ.get("PAC_SERVER_PORT", "8080"))
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8000

# Domains/networks that should GO THROUGH the proxy (others are DIRECT)
PROXY_RULES = []

# Load custom proxy rules from config file if it exists.
# When frozen into an .exe (PyInstaller), look for config.json next to the exe.
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        custom_rules = json.load(f)
        PROXY_RULES.extend(custom_rules.get("proxy_through", []))

def generate_pac():
    """Generate the PAC file content dynamically.
    
    Rules in config.json define which domains/networks should go through the proxy.
    All other traffic goes DIRECT.
    """
    conditions = []

    for rule in PROXY_RULES:
        rtype = rule.get("type", "")
        if rtype == "domain":
            domain_val = rule["value"].lower()
            if "*" in domain_val or "?" in domain_val:
                conditions.append(f"shExpMatch(host, {json.dumps(domain_val)})")
            else:
                domain_val = domain_val.lstrip(".")
                domain_literal = json.dumps(domain_val)
                suffix_literal = json.dumps("." + domain_val)
                conditions.append(
                    f'(host == {domain_literal} || dnsDomainIs(host, {suffix_literal}))'
                )
        elif rtype == "host":
            conditions.append(f'host == {json.dumps(rule["value"].lower())}')
        elif rtype == "range":
            start = json.dumps(rule["start"])
            mask = json.dumps(rule["mask"])
            conditions.append(f"isInNet(host, {start}, {mask})")

    if conditions:
        conditions_str = " ||\n        ".join(conditions)
        pac_content = f"""function FindProxyForURL(url, host) {{
    // Traffic matching these rules goes through the proxy
    if ({conditions_str}) {{
        return "PROXY {PROXY_HOST}:{PROXY_PORT}";
    }}

    // All other traffic goes DIRECT
    return "DIRECT";
}}"""
    else:
        pac_content = f"""function FindProxyForURL(url, host) {{
    // No proxy rules defined — all traffic goes DIRECT
    return "DIRECT";
}}"""
    return pac_content


class PACHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PAC file and proxy configuration."""

    timeout = 60

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/proxy.pac":
            pac_content = generate_pac()
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ns-proxy-autoconfig")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(pac_content.encode("utf-8"))

        elif parsed.path == "/status":
            # Simple status/info endpoint
            info = {
                "status": "running",
                "pac_url": f"http://localhost:{PAC_SERVER_PORT}/proxy.pac",
                "proxy_target": f"{PROXY_HOST}:{PROXY_PORT}",
                "proxy_rules": len(PROXY_RULES),
            }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(info, indent=2).encode("utf-8"))

        elif parsed.path == "/config":
            # Return current configuration as JSON
            config = {"port": PAC_SERVER_PORT, "proxy": f"{PROXY_HOST}:{PROXY_PORT}", "proxy_rules": PROXY_RULES}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(config, indent=2).encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def log_message(self, format, *args):
        """Suppress default logging to keep console clean."""
        pass


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PAC_SERVER_PORT), PACHandler)
    print("=" * 60)
    print("  PAC Proxy Server")
    print("=" * 60)
    print(f"  PAC URL:   http://localhost:{PAC_SERVER_PORT}/proxy.pac")
    print(f"  Status:    http://localhost:{PAC_SERVER_PORT}/status")
    print(f"  Proxy to:  {PROXY_HOST}:{PROXY_PORT}")
    print("-" * 60)
    print("  Set Windows proxy auto-config to the PAC URL above.")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 60)
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
        server.shutdown()


if __name__ == "__main__":
    main()