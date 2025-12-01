/*!
 * ALOPEX Network Management Daemon
 * Enterprise network management without the bloat
 * Onyx Digital Intelligence Development LLC
 */

use anyhow::Result;
use clap::{Parser, Subcommand};
use tokio::net::UnixListener;
use tracing::{info, error};

mod network;
mod bluetooth;
mod ipc;
mod config;

use network::NetworkManager;
use bluetooth::BluetoothManager;
use ipc::IpcServer;
use config::DaemonConfig;

#[derive(Parser)]
#[command(name = "alopexd")]
#[command(about = "ALOPEX Network Management Daemon")]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    /// Configuration file path
    #[arg(short, long, default_value = "/etc/alopex/alopexd.toml")]
    config: String,

    /// Enable debug logging
    #[arg(short, long)]
    debug: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Run the daemon
    Run,
    /// Check daemon status
    Status,
    /// Stop the daemon
    Stop,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    // Initialize logging
    let log_level = if cli.debug { "debug" } else { "info" };
    tracing_subscriber::fmt()
        .with_env_filter(format!("alopex_daemon={}", log_level))
        .init();

    info!("ALOPEX Network Management Daemon starting...");

    // Load configuration
    let config = DaemonConfig::load(&cli.config)?;

    match cli.command.unwrap_or(Commands::Run) {
        Commands::Run => run_daemon(config).await,
        Commands::Status => check_status().await,
        Commands::Stop => stop_daemon().await,
    }
}

async fn run_daemon(config: DaemonConfig) -> Result<()> {
    info!("Initializing network management systems...");

    // Initialize managers
    let network_manager = NetworkManager::new().await?;
    let bluetooth_manager = BluetoothManager::new().await?;

    // Start IPC server
    let listener = UnixListener::bind(&config.socket_path)?;
    let ipc_server = IpcServer::new(listener, network_manager, bluetooth_manager);

    info!("ALOPEX daemon ready on socket: {}", config.socket_path);
    
    // Run the server
    ipc_server.run().await?;

    Ok(())
}

async fn check_status() -> Result<()> {
    println!("ALOPEX daemon status check not implemented yet");
    Ok(())
}

async fn stop_daemon() -> Result<()> {
    println!("ALOPEX daemon stop not implemented yet");
    Ok(())
}