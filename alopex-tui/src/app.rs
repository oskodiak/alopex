use anyhow::Result;
use serde::{Deserialize, Serialize};
use std::time::{Duration, Instant};

use crate::network::{NetworkDiscovery, NetworkMonitor};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name: String,
    pub interface_type: String,
    pub status: String,
    pub ip: Option<String>,
    pub gateway: Option<String>,
    pub dns: Vec<String>,
    pub metrics: NetworkMetrics,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct NetworkMetrics {
    // Traffic counters
    pub bytes_tx: u64,
    pub bytes_rx: u64,
    pub packets_tx: u64,
    pub packets_rx: u64,
    
    // Error counters
    pub errors_tx: u64,
    pub errors_rx: u64,
    pub dropped_tx: u64,
    pub dropped_rx: u64,
    
    // Real-time speeds
    pub speed_up: f64,      // KB/s
    pub speed_down: f64,    // KB/s
    pub packets_per_sec_tx: f64,
    pub packets_per_sec_rx: f64,
    
    // Interface capabilities
    pub link_speed: Option<u32>,  // Mbps
    pub duplex: Option<String>,   // "full", "half", "unknown"
    pub mtu: Option<u32>,
    
    // Connection tracking
    pub uptime: Option<Duration>,
    pub total_session_tx: u64,
    pub total_session_rx: u64,
}

#[derive(Debug)]
pub enum FocusedPanel {
    Interfaces,
    Management,
    Telemetry,
}

pub struct App {
    pub interfaces: Vec<NetworkInterface>,
    pub selected_interface: usize,
    pub focused_panel: FocusedPanel,
    pub telemetry_active: bool,
    pub connection_time: Option<Instant>,
    pub traffic_history: Vec<(f64, f64)>, // (upload, download) history for graph
    socket_path: String,
    network_monitor: NetworkMonitor,
}

impl App {
    pub async fn new(socket_path: &str) -> Result<Self> {
        let mut app = Self {
            interfaces: Vec::new(),
            selected_interface: 0,
            focused_panel: FocusedPanel::Interfaces,
            telemetry_active: false,
            connection_time: None,
            traffic_history: Vec::with_capacity(50), // 5 seconds of history at 100ms intervals
            socket_path: socket_path.to_string(),
            network_monitor: NetworkMonitor::new(),
        };

        // Load initial data
        app.refresh_data().await?;
        Ok(app)
    }

    pub fn previous_interface(&mut self) {
        if !self.interfaces.is_empty() {
            self.selected_interface = if self.selected_interface == 0 {
                self.interfaces.len() - 1
            } else {
                self.selected_interface - 1
            };
        }
    }

    pub fn next_interface(&mut self) {
        if !self.interfaces.is_empty() {
            self.selected_interface = (self.selected_interface + 1) % self.interfaces.len();
        }
    }

    pub fn next_panel(&mut self) {
        self.focused_panel = match self.focused_panel {
            FocusedPanel::Interfaces => FocusedPanel::Management,
            FocusedPanel::Management => FocusedPanel::Telemetry,
            FocusedPanel::Telemetry => FocusedPanel::Interfaces,
        };
    }

    pub async fn toggle_connection(&self) -> Result<()> {
        if let Some(interface) = self.interfaces.get(self.selected_interface) {
            // TODO: Send command to daemon to connect/disconnect interface
            println!("Toggle connection for: {}", interface.name);
        }
        Ok(())
    }

    pub async fn refresh_data(&mut self) -> Result<()> {
        // Discover real network interfaces
        let mut interfaces = NetworkDiscovery::discover_interfaces().await?;
        
        // Sort interfaces by type and name for better organization
        interfaces.sort_by(|a, b| {
            // First sort by type priority
            let type_priority = |interface_type: &str| match interface_type {
                "Ethernet" => 0,
                "WiFi" => 1,
                "VPN" => 2,
                _ => 3,
            };
            
            let type_cmp = type_priority(&a.interface_type).cmp(&type_priority(&b.interface_type));
            if type_cmp != std::cmp::Ordering::Equal {
                return type_cmp;
            }
            
            // Then sort by name (eth0, eth1, wlan0, wlan1, etc.)
            a.name.cmp(&b.name)
        });
        
        self.interfaces = interfaces;

        // Update telemetry state
        self.telemetry_active = self.interfaces.iter().any(|i| i.status == "Connected");
        if self.telemetry_active && self.connection_time.is_none() {
            self.connection_time = Some(Instant::now());
        } else if !self.telemetry_active {
            self.connection_time = None;
        }

        // Ensure we have a valid selection
        if self.selected_interface >= self.interfaces.len() && !self.interfaces.is_empty() {
            self.selected_interface = 0;
        }

        Ok(())
    }

    pub async fn update_metrics(&mut self) -> Result<()> {
        // Get fresh interface metrics
        let fresh_interfaces = NetworkDiscovery::discover_interfaces().await?;
        
        // Update our interfaces with fresh data, preserving uptime tracking
        for fresh in fresh_interfaces {
            if let Some(existing) = self.interfaces.iter_mut().find(|i| i.name == fresh.name) {
                let old_uptime = existing.metrics.uptime;
                *existing = fresh;
                existing.metrics.uptime = old_uptime;
            }
        }
        
        // Calculate speed differences using the monitor
        self.network_monitor.update_speeds(&mut self.interfaces);
        
        if self.telemetry_active {
            // Update traffic history for sparkline graphs
            if let Some(interface) = self.interfaces.get(self.selected_interface) {
                let upload = interface.metrics.speed_up;
                let download = interface.metrics.speed_down;
                
                self.traffic_history.push((upload, download));
                if self.traffic_history.len() > 50 {
                    self.traffic_history.remove(0);
                }
            }
            
            // Update uptime for connected interfaces
            if let Some(interface) = self.interfaces.get_mut(self.selected_interface) {
                if interface.status == "Connected" {
                    if let Some(start_time) = self.connection_time {
                        interface.metrics.uptime = Some(start_time.elapsed());
                    } else {
                        self.connection_time = Some(Instant::now());
                        interface.metrics.uptime = Some(Duration::from_secs(0));
                    }
                }
            }
        }
        
        Ok(())
    }

    pub fn get_selected_interface(&self) -> Option<&NetworkInterface> {
        self.interfaces.get(self.selected_interface)
    }
}