pub mod ethernet;
pub mod wifi;
pub mod vpn;

use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tokio::sync::RwLock;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub id: Uuid,
    pub name: String,
    pub interface_type: InterfaceType,
    pub status: ConnectionStatus,
    pub config: InterfaceConfig,
    pub metrics: NetworkMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InterfaceType {
    Ethernet,
    WiFi,
    VPN,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConnectionStatus {
    Disconnected,
    Connecting,
    Connected,
    Error(String),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum InterfaceConfig {
    Ethernet {
        dhcp: bool,
        ip: Option<String>,
        gateway: Option<String>,
        dns: Vec<String>,
    },
    WiFi {
        ssid: String,
        security: WiFiSecurity,
        dhcp: bool,
        ip: Option<String>,
    },
    VPN {
        provider: String,
        config_path: String,
        auto_connect: bool,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WiFiSecurity {
    Open,
    WPA2(String),
    WPA3(String),
    Enterprise,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct NetworkMetrics {
    pub bytes_tx: u64,
    pub bytes_rx: u64,
    pub packets_tx: u64,
    pub packets_rx: u64,
    pub speed_up: f64,    // KB/s
    pub speed_down: f64,  // KB/s
    pub link_speed: Option<u32>,  // Mbps
    pub signal_strength: Option<i32>, // dBm for WiFi
}

pub struct NetworkManager {
    interfaces: RwLock<HashMap<String, NetworkInterface>>,
}

impl NetworkManager {
    pub async fn new() -> Result<Self> {
        let manager = Self {
            interfaces: RwLock::new(HashMap::new()),
        };
        
        // Discover existing interfaces
        manager.discover_interfaces().await?;
        
        Ok(manager)
    }

    async fn discover_interfaces(&self) -> Result<()> {
        // TODO: Discover ethernet interfaces via netlink
        // TODO: Discover WiFi interfaces via iwd
        Ok(())
    }

    pub async fn get_interfaces(&self) -> Vec<NetworkInterface> {
        self.interfaces.read().await.values().cloned().collect()
    }

    pub async fn get_interface(&self, name: &str) -> Option<NetworkInterface> {
        self.interfaces.read().await.get(name).cloned()
    }
}