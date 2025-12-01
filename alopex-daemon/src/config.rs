use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Debug, Deserialize, Serialize)]
pub struct DaemonConfig {
    pub socket_path: String,
    pub network: NetworkConfig,
    pub bluetooth: BluetoothConfig,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct NetworkConfig {
    pub auto_connect: bool,
    pub ethernet_priority: u32,
    pub wifi_priority: u32,
    pub vpn_priority: u32,
}

#[derive(Debug, Deserialize, Serialize)]
pub struct BluetoothConfig {
    pub enabled: bool,
    pub auto_connect_trusted: bool,
    pub discoverable_timeout: u32,
}

impl Default for DaemonConfig {
    fn default() -> Self {
        Self {
            socket_path: "/run/alopex/alopex.sock".to_string(),
            network: NetworkConfig {
                auto_connect: true,
                ethernet_priority: 100,
                wifi_priority: 50,
                vpn_priority: 200,
            },
            bluetooth: BluetoothConfig {
                enabled: true,
                auto_connect_trusted: true,
                discoverable_timeout: 300,
            },
        }
    }
}

impl DaemonConfig {
    pub fn load(path: &str) -> Result<Self> {
        match fs::read_to_string(path) {
            Ok(content) => Ok(toml::from_str(&content)?),
            Err(_) => {
                // Create default config if not found
                let config = Self::default();
                let _ = fs::write(path, toml::to_string_pretty(&config)?);
                Ok(config)
            }
        }
    }
}