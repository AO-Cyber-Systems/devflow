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

// ============================================================
// Setup / Prerequisites Types
// ============================================================

export type ToolCategory =
  | 'code_editor'
  | 'runtime'
  | 'container'
  | 'database'
  | 'secrets'
  | 'version_control'
  | 'cli_utility'
  | 'shell'
  | 'infrastructure';

export type InstallStatus =
  | 'installed'
  | 'not_installed'
  | 'outdated'
  | 'installing'
  | 'failed';

export type PackageManager =
  | 'brew'
  | 'apt'
  | 'dnf'
  | 'yum'
  | 'pacman'
  | 'zypper'
  | 'snap'
  | 'flatpak'
  | 'winget'
  | 'scoop'
  | 'choco'
  | 'mise'
  | 'npm'
  | 'pipx';

export interface PlatformInfo {
  os: 'linux' | 'macos' | 'windows' | 'unknown';
  distro: string | null;
  architecture: 'x86_64' | 'arm64' | 'armv7' | 'unknown';
  is_wsl: boolean;
  package_managers: PackageManager[];
  is_macos: boolean;
  is_linux: boolean;
  is_windows: boolean;
}

export interface ToolInfo {
  id: string;
  name: string;
  description: string;
  category: ToolCategory;
  command: string;
  website: string;
  essential: boolean;
  mise_managed: boolean;
  install_methods: {
    brew_package: string | null;
    brew_cask: string | null;
    apt_package: string | null;
    snap_package: string | null;
    snap_classic: boolean;
    winget_id: string | null;
    scoop_package: string | null;
    mise_package: string | null;
    npm_package: string | null;
  };
}

export interface ToolStatus {
  tool_id: string;
  name: string;
  category?: ToolCategory;
  status: InstallStatus;
  version: string | null;
  path?: string | null;
  install_methods: PackageManager[];
  installed_via?: PackageManager | null;
}

export interface InstallMethod {
  method: PackageManager;
  available: boolean;
  package: string | null;
  is_cask?: boolean;
  classic?: boolean;
  managed_by_mise?: boolean;
}

export interface InstallMethodsResult {
  tool_id: string;
  name: string;
  methods: InstallMethod[];
  recommended: PackageManager | null;
}

export interface InstallResult {
  success: boolean;
  message: string;
  version?: string | null;
  error_details?: string | null;
  requires_restart?: boolean;
}

export interface MultiInstallResult {
  total: number;
  success_count: number;
  failed_count: number;
  results: Array<{ tool_id: string } & InstallResult>;
}

export interface PrerequisitesSummary {
  total: number;
  installed: number;
  not_installed: number;
  outdated: number;
  by_category: Record<
    ToolCategory,
    {
      total: number;
      installed: number;
    }
  >;
}

export interface CategoryInfo {
  name: string;
  tool_count: number;
  tool_ids: string[];
}

export interface InstallerInfo {
  package_manager: PackageManager;
  name: string;
}

export interface MiseStatus {
  available: boolean;
  version?: string | null;
  install_hint?: string | null;
  error?: string;
}

// ============================================================
// Backend Setup Types
// ============================================================

/**
 * Backend type enumeration
 */
export type BackendType = 'local_python' | 'docker' | 'wsl2' | 'remote';

/**
 * Backend configuration for connecting to the Python bridge
 */
export interface BackendConfig {
  /** The type of backend */
  backend_type: BackendType;
  /** Path to Python executable (for local_python) */
  python_path: string | null;
  /** Docker container name (for docker) */
  container_name: string | null;
  /** WSL distribution name (for wsl2) */
  wsl_distro: string | null;
  /** Remote host (for remote, docker, wsl2) */
  remote_host: string | null;
  /** Remote port (for remote, docker, wsl2) - defaults to 9876 */
  remote_port: number | null;
  /** Whether to auto-start the backend on app launch */
  auto_start: boolean;
}

/**
 * Global backend configuration stored at ~/.devflow/backend.json
 */
export interface GlobalBackendConfig {
  /** The default backend configuration */
  default_backend: BackendConfig | null;
  /** Whether the backend has been configured at least once */
  configured: boolean;
}

/**
 * Prerequisite detection status
 */
export interface PrerequisiteStatus {
  /** Python availability */
  python_available: boolean;
  /** Python version string (e.g., "3.11.5") */
  python_version: string | null;
  /** Path to Python executable */
  python_path: string | null;
  /** Whether devflow package is installed */
  devflow_installed: boolean;
  /** DevFlow package version */
  devflow_version: string | null;
  /** Docker availability */
  docker_available: boolean;
  /** Whether Docker daemon is running */
  docker_running: boolean;
  /** Docker version string */
  docker_version: string | null;
  /** WSL2 availability (Windows only) */
  wsl_available: boolean;
  /** List of available WSL distributions */
  wsl_distros: string[];
}

/**
 * Setup wizard step
 */
export type WizardStep =
  | 'welcome'
  | 'detecting'
  | 'selection'
  | 'installing'
  | 'connecting'
  | 'complete'
  | 'error';

/**
 * Setup wizard state
 */
export interface WizardState {
  step: WizardStep;
  prerequisites: PrerequisiteStatus | null;
  selectedBackend: BackendType | null;
  config: BackendConfig | null;
  installProgress: number;
  error: string | null;
}
