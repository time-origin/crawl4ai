
import os
import subprocess

# The special 'host.docker.internal' resolves to the host machine's IP from within the container.
# We get the proxy URL from an environment variable, defaulting to Clash's common HTTP port (7890).
PROXY_URL = os.environ.get("PROXY_URL", "http://host.docker.internal:7890")
TARGET_URL = "https://x.com"

print("="*60)
print("Proxy Connectivity Test")
print("="*60)
print(f"Attempting to connect to: {TARGET_URL}")
print(f"Using proxy server:      {PROXY_URL}")
print("="*60)

# Environment for the subprocess. curl respects these variables.
proxy_env = os.environ.copy()
proxy_env["http_proxy"] = PROXY_URL
proxy_env["https_proxy"] = PROXY_URL
proxy_env["no_proxy"] = "localhost,127.0.0.1"

# Command to execute. -L follows redirects, which is important for sites like x.com.
command = ["curl", "-L", "--verbose", TARGET_URL]

try:
    # Execute the command with a 30-second timeout
    result = subprocess.run(
        command,
        env=proxy_env,
        capture_output=True,
        text=True,
        check=True,  # This will raise an exception if curl returns a non-zero exit code
        timeout=30
    )
    print("\n--- SUCCESS: Page content received ---")
    print("The container can successfully access x.com through the host's proxy.\n")
    print("First 500 characters of the page:")
    print(result.stdout[:500])

except subprocess.CalledProcessError as e:
    print("\n--- ❌ ERROR: curl command failed ---")
    print(f"Curl exited with a non-zero status code: {e.returncode}")
    print("\nThis usually means the proxy is reachable, but the target site blocked the request or had an error.")
    print("\n--- STDERR (Error Details from curl) ---")
    print(e.stderr)

except subprocess.TimeoutExpired:
    print("\n--- ❌ ERROR: Connection Timed Out ---")
    print("The request took longer than 30 seconds.")
    print("This often points to a problem with the proxy server or the VPN connection itself.")

except Exception as e:
    print(f"\n--- ❌ An unexpected script error occurred: {e} ---")
    print("\nThis might indicate a problem with the script itself or the container environment.")
