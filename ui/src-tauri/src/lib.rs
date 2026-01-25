mod bridge;
mod commands;

use bridge::BridgeManager;
use std::sync::Arc;
use tauri_plugin_log::{Target, TargetKind};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Initialize bridge manager
    let bridge_manager = Arc::new(BridgeManager::new());

    // Build log plugin with explicit targets
    let log_plugin = tauri_plugin_log::Builder::default()
        .level(log::LevelFilter::Debug)
        .targets([
            Target::new(TargetKind::Stdout),
            Target::new(TargetKind::LogDir { file_name: None }),
            Target::new(TargetKind::Webview),
        ])
        .build();

    tauri::Builder::default()
        .manage(bridge_manager)
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(log_plugin)
        .invoke_handler(tauri::generate_handler![
            // Bridge management
            commands::get_bridge_status,
            commands::start_bridge,
            commands::stop_bridge,
            // Config
            commands::config::get_global_config,
            commands::config::get_project_config,
            commands::config::update_global_config,
            commands::config::update_project_config,
            commands::config::validate_config,
            // Projects
            commands::projects::list_projects,
            commands::projects::add_project,
            commands::projects::remove_project,
            commands::projects::get_project_status,
            commands::projects::open_project_folder,
            commands::projects::init_project,
            // Infrastructure
            commands::infra::get_infra_status,
            commands::infra::start_infra,
            commands::infra::stop_infra,
            commands::infra::configure_project_infra,
            commands::infra::unconfigure_project_infra,
            commands::infra::regenerate_certs,
            commands::infra::manage_hosts,
            // Database
            commands::database::get_migration_status,
            commands::database::run_migrations,
            commands::database::rollback_migrations,
            commands::database::create_migration,
            commands::database::get_migration_history,
            commands::database::test_db_connection,
            // Deploy
            commands::deploy::get_deploy_status,
            commands::deploy::deploy,
            commands::deploy::rollback_deploy,
            commands::deploy::get_deploy_logs,
            commands::deploy::get_ssh_command,
            // Secrets
            commands::secrets::list_secrets,
            commands::secrets::sync_secrets,
            commands::secrets::verify_secrets,
            commands::secrets::export_secrets,
            commands::secrets::get_secret_providers,
            // Development
            commands::dev::get_dev_status,
            commands::dev::start_dev,
            commands::dev::stop_dev,
            commands::dev::restart_dev_service,
            commands::dev::get_dev_logs,
            commands::dev::exec_in_container,
            commands::dev::reset_dev,
            commands::dev::setup_dev,
            // System
            commands::system::run_doctor,
            commands::system::run_project_doctor,
            commands::system::get_system_info,
            commands::system::get_provider_status,
            commands::system::get_all_providers,
            commands::system::check_updates,
            commands::system::get_version,
            // Setup / Prerequisites
            commands::setup::get_platform_info,
            commands::setup::get_tool_categories,
            commands::setup::get_all_tools,
            commands::setup::get_essential_tools,
            commands::setup::get_tools_by_category,
            commands::setup::get_tool,
            commands::setup::detect_tool,
            commands::setup::detect_all_tools,
            commands::setup::detect_essential_tools,
            commands::setup::get_install_methods,
            commands::setup::install_tool,
            commands::setup::install_multiple_tools,
            commands::setup::check_mise_available,
            commands::setup::get_mise_installed_tools,
            commands::setup::get_available_installers,
            commands::setup::get_prerequisites_summary,
            commands::setup::refresh_platform_info,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
