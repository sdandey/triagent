#!/usr/bin/env python3
"""Validate Triagent API deployment.

Usage:
    python scripts/validate-deployment.py
    python scripts/validate-deployment.py --url https://custom-app.azurewebsites.net
"""

import argparse
import json
import os
import subprocess
import sys
import time

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)


class DeploymentValidator:
    """Validate deployed Triagent API."""

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        az_cmd: str = "az-elevated",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.az_cmd = az_cmd
        self.session_id: str | None = None
        self.test_email: str | None = None
        self.results: dict[str, bool | str] = {}

    def _run_az_cmd(self, args: list[str]) -> str | None:
        """Run Azure CLI command and return output."""
        try:
            result = subprocess.run(
                [self.az_cmd] + args,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception as e:
            print(f"   Warning: Azure CLI command failed: {e}")
        return None

    def _get_api_key_from_azure(self) -> str | None:
        """Get API key from App Service settings."""
        output = self._run_az_cmd([
            "webapp", "config", "appsettings", "list",
            "--name", "triagent-sandbox-app",
            "--resource-group", "triagent-sandbox-rg",
            "--query", "[?name=='TRIAGENT_API_KEY'].value",
            "-o", "tsv",
        ])
        return output if output else None

    def validate_health(self) -> bool:
        """Test /health endpoint."""
        print("\n1. Testing /health endpoint...")
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Status: {data.get('status')}")
                    print(f"   Version: {data.get('version')}")
                    self.results["health"] = True
                    return True
                elif response.status_code == 403:
                    print("   403 Forbidden - Network/IP restriction")
                    print("   This is expected from corporate networks.")
                    self.results["health"] = "blocked"
                    return False
                else:
                    print(f"   HTTP {response.status_code}: {response.text[:100]}")
                    self.results["health"] = False
                    return False
        except Exception as e:
            print(f"   Error: {e}")
            self.results["health"] = False
            return False

    def validate_azure_resources(self) -> bool:
        """Validate Azure resources via CLI."""
        print("\n2. Checking Azure resources...")

        # Check App Service
        app_state = self._run_az_cmd([
            "webapp", "show",
            "--name", "triagent-sandbox-app",
            "--resource-group", "triagent-sandbox-rg",
            "--query", "{state: state, container: siteConfig.linuxFxVersion}",
            "-o", "json",
        ])
        if app_state:
            try:
                data = json.loads(app_state)
                print(f"   App Service State: {data.get('state')}")
                print(f"   Container: {data.get('container')}")
                self.results["app_service"] = data.get("state") == "Running"
            except json.JSONDecodeError:
                self.results["app_service"] = False

        # Check Session Pool
        pool_state = self._run_az_cmd([
            "containerapp", "sessionpool", "show",
            "--name", "triagent-sandbox-session-pool",
            "--resource-group", "triagent-sandbox-rg",
            "--query", "{endpoint: properties.poolManagementEndpoint, readyCount: properties.templateUpdateStatus.activeTemplate.status.readyCount}",
            "-o", "json",
        ])
        if pool_state:
            try:
                data = json.loads(pool_state)
                print(f"   Session Pool Endpoint: {data.get('endpoint')}")
                print(f"   Ready Instances: {data.get('readyCount')}")
                self.results["session_pool"] = data.get("readyCount", 0) > 0
            except json.JSONDecodeError:
                self.results["session_pool"] = False

        return bool(self.results.get("app_service")) and bool(
            self.results.get("session_pool")
        )

    def validate_session_pool_api(self) -> bool:
        """Test Session Pool API directly."""
        print("\n3. Testing Session Pool API...")

        # Get endpoint
        endpoint = self._run_az_cmd([
            "containerapp", "sessionpool", "show",
            "--name", "triagent-sandbox-session-pool",
            "--resource-group", "triagent-sandbox-rg",
            "--query", "properties.poolManagementEndpoint",
            "-o", "tsv",
        ])
        if not endpoint:
            print("   Could not get Session Pool endpoint")
            self.results["session_pool_api"] = False
            return False

        # Get token
        token = self._run_az_cmd([
            "account", "get-access-token",
            "--resource", "https://dynamicsessions.io",
            "--query", "accessToken",
            "-o", "tsv",
        ])
        if not token:
            print("   Could not get Azure token for dynamicsessions.io")
            self.results["session_pool_api"] = False
            return False

        print(f"   Endpoint: {endpoint}")
        print("   Token acquired")

        # Test code execution
        session_id = f"validate-{int(time.time())}"
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{endpoint}/code/execute",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Identifier": session_id,
                        "Content-Type": "application/json",
                    },
                    json={
                        "properties": {
                            "codeInputType": "inline",
                            "executionType": "synchronous",
                            "code": "print('Hello from Session Pool validation')",
                        }
                    },
                )
                if response.status_code == 200:
                    result = response.json()
                    stdout = result.get("properties", {}).get("stdout", "")
                    print(f"   Execution: Success")
                    print(f"   Output: {stdout.strip()}")
                    self.results["session_pool_api"] = True
                    return True
                elif response.status_code == 403:
                    print("   403 Forbidden - Missing Session Executor role")
                    print("   Your identity needs 'Azure ContainerApps Session Executor' role.")
                    self.results["session_pool_api"] = "forbidden"
                    return False
                else:
                    print(f"   HTTP {response.status_code}: {response.text[:200]}")
                    self.results["session_pool_api"] = False
                    return False
        except Exception as e:
            print(f"   Error: {e}")
            self.results["session_pool_api"] = False
            return False

    def run_all(self) -> bool:
        """Run all validations."""
        print(f"\n{'='*60}")
        print("Triagent Deployment Validation")
        print(f"{'='*60}")
        print(f"URL: {self.base_url}")
        print(f"Azure CLI: {self.az_cmd}")

        self.validate_health()
        self.validate_azure_resources()
        self.validate_session_pool_api()

        print(f"\n{'='*60}")
        print("Summary")
        print(f"{'='*60}")

        critical_passed = True
        for name, result in self.results.items():
            if result is True:
                status = "PASS"
            elif result == "blocked" or result == "forbidden":
                status = "BLOCKED (network/role)"
            else:
                status = "FAIL"
                if name in ["app_service", "session_pool"]:
                    critical_passed = False

            print(f"  {name}: {status}")

        if critical_passed:
            print("\n Azure resources are configured correctly.")
            print("  Network access may be blocked from your location.")
            print("\n  To test from Azure Portal:")
            print("    1. Go to App Service > Development Tools > Console")
            print("    2. Run: curl http://localhost:8080/health")
        else:
            print("\n Azure resources have issues. Check the errors above.")

        return critical_passed


def main():
    parser = argparse.ArgumentParser(description="Validate Triagent API deployment")
    parser.add_argument(
        "--url",
        default="https://triagent-sandbox-app.azurewebsites.net",
        help="App Service URL",
    )
    parser.add_argument(
        "--az-cmd",
        default="az-elevated",
        help="Azure CLI command (default: az-elevated)",
    )
    parser.add_argument(
        "--api-key",
        help="API key (or fetched from Azure)",
    )
    args = parser.parse_args()

    validator = DeploymentValidator(args.url, args.api_key, args.az_cmd)
    success = validator.run_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
