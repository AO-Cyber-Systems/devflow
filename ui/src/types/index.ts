/**
 * TypeScript types matching DevFlow Pydantic models
 */

// ============================================================
// Global Configuration
// ============================================================

export interface GlobalGitConfig {
  user_name: string | null;
  user_email: string | null;
  co_author_enabled: boolean;
  co_author_name: string;
  co_author_email: string;
}

export interface GlobalDefaultsConfig {
  secrets_provider: string | null;
  network_name: string;
  registry: string | null;
}

export interface GlobalInfrastructureConfig {
  auto_start: boolean;
  traefik_http_port: number;
  traefik_https_port: number;
  traefik_dashboard_port: number;
}

export interface GlobalConfig {
  version: string;
  git: GlobalGitConfig;
  defaults: GlobalDefaultsConfig;
  infrastructure: GlobalInfrastructureConfig;
  setup_completed: boolean;
}

// ============================================================
// Project Configuration
// ============================================================

export interface ProjectConfig {
  name: string;
  preset: string | null;
}

export interface MigrationsConfig {
  directory: string;
  format: string;
  tracking_table: string;
  tracking_schema: string;
  use_supabase_cli: boolean;
}

export interface DatabaseEnvConfig {
  url_env: string | null;
  url_secret: string | null;
  host: string | null;
  ssh_user: string | null;
  direct_port: number | null;
  require_approval: boolean;
}

export interface DatabaseConfig {
  migrations: MigrationsConfig;
  environments: Record<string, DatabaseEnvConfig>;
}

export interface SecretMapping {
  name: string;
  op_item: string | null;
  op_field: string | null;
  github_secret: string | null;
  docker_secret: string | null;
}

export interface GitHubAppConfig {
  app_id: string;
  installation_id: string;
  private_key: string;
}

export interface GitHubConfig {
  auth: 'cli' | 'app';
  app: GitHubAppConfig | null;
}

export interface SecretsConfig {
  provider: string | null;
  vault: string | null;
  github: GitHubConfig | null;
  mappings: SecretMapping[];
}

export interface ServiceConfig {
  image: string;
  stack: string;
  replicas: number;
  health_endpoint: string | null;
}

export interface DeploymentEnvConfig {
  host: string | null;
  ssh_user: string;
  ssh_key_secret: string | null;
  auto_deploy_branch: string | null;
  require_approval: boolean;
  approval_environment: string | null;
}

export interface DeploymentConfig {
  registry: string | null;
  organization: string | null;
  services: Record<string, ServiceConfig>;
  environments: Record<string, DeploymentEnvConfig>;
}

export interface DevelopmentConfig {
  compose_file: string;
  services: string[];
  env: Record<string, string>;
  ports: Record<string, number>;
}

export interface TraefikConfig {
  http_port: number;
  https_port: number;
  dashboard_port: number;
  dashboard_enabled: boolean;
  log_level: string;
}

export interface CertificatesConfig {
  domains: string[];
  cert_dir: string;
}

export interface InfrastructureConfig {
  enabled: boolean;
  network_name: string;
  legacy_networks: string[];
  traefik: TraefikConfig;
  certificates: CertificatesConfig;
}

export interface GitUserConfig {
  name: string | null;
  email: string | null;
}

export interface GitCoAuthorConfig {
  enabled: boolean;
  name: string;
  email: string;
}

export interface GitConfig {
  user: GitUserConfig;
  co_author: GitCoAuthorConfig;
}

export interface DevflowConfig {
  version: string;
  project: ProjectConfig;
  database: DatabaseConfig | null;
  secrets: SecretsConfig | null;
  deployment: DeploymentConfig | null;
  development: DevelopmentConfig | null;
  infrastructure: InfrastructureConfig | null;
  git: GitConfig | null;
}

// ============================================================
// Status & Result Types
// ============================================================

export interface Project {
  name: string;
  path: string;
  configured_at: string | null;
  last_accessed: string | null;
  exists?: boolean;
  has_devflow_config?: boolean;
}

export interface ProjectStatus {
  name: string;
  path: string;
  has_devflow_config: boolean;
  infrastructure_enabled: boolean;
  services_running: number;
  services_total: number;
}

export interface InfraStatus {
  network_exists: boolean;
  network_name: string;
  traefik_running: boolean;
  traefik_container_id: string | null;
  traefik_url: string | null;
  certificates_valid: boolean;
  certificates_path: string | null;
  registered_projects: RegisteredProject[];
}

export interface RegisteredProject {
  name: string;
  path: string;
  domains: string[];
  compose_files: string[];
  configured_at: string;
  backup_path: string | null;
}

export interface MigrationStatus {
  environment: string;
  executor: string;
  applied: number;
  pending: number;
  total: number;
  pending_files: string[];
}

export interface ContainerStatus {
  name: string;
  image: string;
  status: 'running' | 'stopped' | 'exited' | 'paused';
  ports: string[];
  health: 'healthy' | 'unhealthy' | 'starting' | null;
}

export interface DevStatus {
  project: string;
  services: ContainerStatus[];
  infrastructure_connected: boolean;
}

export interface DeployStatus {
  environment: string;
  host: string | null;
  services: ServiceStatus[];
  last_deploy: string | null;
}

export interface ServiceStatus {
  name: string;
  image: string;
  replicas: string;
  status: 'running' | 'stopped' | 'partial' | 'unknown';
  last_updated: string | null;
}

export interface DoctorCheck {
  name: string;
  category: 'tool' | 'auth' | 'config' | 'infrastructure';
  status: 'ok' | 'warning' | 'error' | 'skipped';
  message: string;
  details?: Record<string, unknown>;
  fix_hint?: string;
}

export interface DoctorResult {
  overall_status: 'healthy' | 'warning' | 'error';
  checks: DoctorCheck[];
}

export interface ProviderStatus {
  name: string;
  binary: string;
  available: boolean;
  authenticated: boolean;
  version: string | null;
  path: string | null;
}

export interface SystemInfo {
  platform: string;
  os_version: string;
  devflow_version: string;
  python_version: string;
  docker_version: string | null;
  home_dir: string;
  config_dir: string;
}

// ============================================================
// API Response Types
// ============================================================

export interface CommandResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}

export interface OperationResult {
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
}

export interface ListResponse<T> {
  items: T[];
  total: number;
}

// ============================================================
// Bridge Types
// ============================================================

export type BridgeState = 'Stopped' | 'Starting' | 'Running' | 'Error';
