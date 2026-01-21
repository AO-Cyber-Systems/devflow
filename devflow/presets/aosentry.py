"""AOSentry preset configuration."""

from typing import Any

from devflow.presets.base import Preset


class AOSentryPreset(Preset):
    """Preset for AOSentry AI gateway and observability platform."""

    @property
    def name(self) -> str:
        return "aosentry"

    @property
    def description(self) -> str:
        return "AOSentry AI gateway and observability platform"

    def get_config(self) -> dict[str, Any]:
        return {
            "version": "1",
            "project": {
                "name": "aosentry",
                "preset": "aosentry",
            },
            "database": {
                "migrations": {
                    "directory": "supabase/migrations",
                    "format": "sql",
                    "tracking_table": "schema_migrations",
                    "tracking_schema": "public",
                },
                "environments": {
                    "local": {
                        "url_env": "DATABASE_URL",
                    },
                    "staging": {
                        "url_secret": "aosentry_database_url",
                        "host": "ao-staging-manager",
                        "ssh_user": "deploy",
                    },
                    "production": {
                        "url_secret": "aosentry_database_url",
                        "host": "aosentry-production-manager",
                        "ssh_user": "deploy",
                        "require_approval": True,
                    },
                },
            },
            "secrets": {
                "provider": "1password",
                "vault": "AOCyber",
                "mappings": [
                    {
                        "name": "database_url",
                        "op_item": "AOSentry Database",
                        "op_field": "connection_string",
                        "github_secret": "DATABASE_URL",
                        "docker_secret": "aosentry_database_url",
                    },
                    {
                        "name": "master_key",
                        "op_item": "AOSentry",
                        "op_field": "master_key",
                        "github_secret": "AOSENTRY_MASTER_KEY",
                        "docker_secret": "aosentry_master_key",
                    },
                    {
                        "name": "salt_key",
                        "op_item": "AOSentry",
                        "op_field": "salt_key",
                        "github_secret": "AOSENTRY_SALT_KEY",
                        "docker_secret": "aosentry_salt_key",
                    },
                    {
                        "name": "jwt_secret",
                        "op_item": "AOSentry Supabase",
                        "op_field": "jwt_secret",
                        "github_secret": "SUPABASE_JWT_SECRET",
                        "docker_secret": "aosentry_jwt_secret",
                    },
                    {
                        "name": "anon_key",
                        "op_item": "AOSentry Supabase",
                        "op_field": "anon_key",
                        "github_secret": "SUPABASE_ANON_KEY",
                        "docker_secret": "aosentry_anon_key",
                    },
                    {
                        "name": "service_role_key",
                        "op_item": "AOSentry Supabase",
                        "op_field": "service_role_key",
                        "github_secret": "SUPABASE_SERVICE_ROLE_KEY",
                        "docker_secret": "aosentry_service_role_key",
                    },
                ],
            },
            "deployment": {
                "registry": "ghcr.io",
                "organization": "ao-cyber-systems",
                "services": {
                    "proxy": {
                        "image": "aosentry",
                        "stack": "aosentry",
                        "replicas": 2,
                        "health_endpoint": "/health",
                    },
                    "dashboard": {
                        "image": "aosentry-dashboard",
                        "stack": "aosentry",
                        "replicas": 1,
                        "health_endpoint": "/",
                    },
                },
                "environments": {
                    "staging": {
                        "host": "ao-staging-manager",
                        "ssh_user": "deploy",
                        "ssh_key_secret": "STAGING_SSH_KEY",
                        "auto_deploy_branch": "main",
                    },
                    "production": {
                        "host": "aosentry-production-manager",
                        "ssh_user": "deploy",
                        "ssh_key_secret": "PRODUCTION_SSH_KEY",
                        "require_approval": True,
                        "approval_environment": "production",
                    },
                },
            },
            "development": {
                "compose_file": "docker-compose.yml",
                "services": ["db", "proxy", "dashboard"],
                "env": {
                    "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/aosentry",
                },
                "ports": {
                    "proxy": 4000,
                    "dashboard": 3000,
                    "db": 5432,
                },
            },
        }
