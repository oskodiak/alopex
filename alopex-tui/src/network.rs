/*!
 * Real Network Interface Discovery and Metrics
 * Direct system integration for live network data
 */

use anyhow::Result;
use std::fs;
use std::collections::HashMap;

use crate::app::{NetworkInterface, NetworkMetrics};

pub struct NetworkDiscovery;

impl NetworkDiscovery {
    pub async fn discover_interfaces() -> Result<Vec<NetworkInterface>> {
        let mut interfaces = Vec::new();
        
        // Read all network interfaces from /sys/class/net/
        let net_dir = "/sys/class/net";
        if let Ok(entries) = fs::read_dir(net_dir) {
            for entry in entries.flatten() {
                let interface_name = entry.file_name().to_string_lossy().to_string();
                
                // Skip loopback
                if interface_name == "lo" {
                    continue;
                }
                
                if let Ok(interface) = Self::get_interface_info(&interface_name).await {
                    interfaces.push(interface);
                }
            }
        }
        
        Ok(interfaces)
    }

    async fn get_interface_info(name: &str) -> Result<NetworkInterface> {
        let interface_type = Self::detect_interface_type(name)?;
        let status = Self::get_interface_status(name)?;
        let ip = Self::get_interface_ip(name)?;
        let gateway = Self::get_default_gateway()?;
        let dns = Self::get_dns_servers()?;
        let metrics = Self::get_interface_metrics(name)?;

        Ok(NetworkInterface {
            name: name.to_string(),
            interface_type,
            status,
            ip,
            gateway,
            dns,
            metrics,
        })
    }

    fn detect_interface_type(name: &str) -> Result<String> {
        // Check interface type based on name patterns and sysfs
        if name.starts_with("eth") || name.starts_with("en") {
            Ok("Ethernet".to_string())
        } else if name.starts_with("wlan") || name.starts_with("wl") {
            Ok("WiFi".to_string())
        } else if name.starts_with("tun") || name.starts_with("wg") {
            Ok("VPN".to_string())
        } else {
            Ok("Unknown".to_string())
        }
    }

    fn get_interface_status(name: &str) -> Result<String> {
        // Check if interface is up
        let operstate_path = format!("/sys/class/net/{}/operstate", name);
        match fs::read_to_string(&operstate_path) {
            Ok(state) => {
                let state = state.trim();
                match state {
                    "up" => Ok("Connected".to_string()),
                    "down" => Ok("Disconnected".to_string()),
                    "dormant" => Ok("Connecting".to_string()),
                    _ => Ok("Unknown".to_string()),
                }
            }
            Err(_) => Ok("Unknown".to_string()),
        }
    }

    fn get_interface_ip(name: &str) -> Result<Option<String>> {
        // Parse ip addr show output for interface
        use std::process::Command;
        
        let output = Command::new("ip")
            .args(["addr", "show", name])
            .output()?;
            
        let output_str = String::from_utf8_lossy(&output.stdout);
        
        // Look for inet lines
        for line in output_str.lines() {
            if line.trim().starts_with("inet ") && !line.contains("127.0.0.1") {
                if let Some(ip_part) = line.trim().split_whitespace().nth(1) {
                    // Extract just the IP without CIDR
                    if let Some(ip) = ip_part.split('/').next() {
                        return Ok(Some(ip.to_string()));
                    }
                }
            }
        }
        
        Ok(None)
    }

    fn get_default_gateway() -> Result<Option<String>> {
        use std::process::Command;
        
        let output = Command::new("ip")
            .args(["route", "show", "default"])
            .output()?;
            
        let output_str = String::from_utf8_lossy(&output.stdout);
        
        // Parse "default via X.X.X.X dev..."
        for line in output_str.lines() {
            if line.contains("default via") {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if let Some(pos) = parts.iter().position(|&x| x == "via") {
                    if let Some(gateway) = parts.get(pos + 1) {
                        return Ok(Some(gateway.to_string()));
                    }
                }
            }
        }
        
        Ok(None)
    }

    fn get_dns_servers() -> Result<Vec<String>> {
        // Read /etc/resolv.conf
        match fs::read_to_string("/etc/resolv.conf") {
            Ok(content) => {
                let mut dns_servers = Vec::new();
                for line in content.lines() {
                    if line.starts_with("nameserver ") {
                        if let Some(dns) = line.split_whitespace().nth(1) {
                            dns_servers.push(dns.to_string());
                        }
                    }
                }
                Ok(dns_servers)
            }
            Err(_) => Ok(vec!["8.8.8.8".to_string()]), // Fallback
        }
    }

    fn get_interface_metrics(name: &str) -> Result<NetworkMetrics> {
        // Read /proc/net/dev for interface statistics
        let proc_net_dev = fs::read_to_string("/proc/net/dev")?;
        
        for line in proc_net_dev.lines().skip(2) { // Skip header lines
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.is_empty() {
                continue;
            }
            
            let interface_part = parts[0].trim_end_matches(':');
            if interface_part == name && parts.len() >= 17 {
                // Parse all available fields from /proc/net/dev
                // Format: interface: bytes packets errs drop fifo frame compressed multicast
                let bytes_rx = parts[1].parse::<u64>().unwrap_or(0);
                let packets_rx = parts[2].parse::<u64>().unwrap_or(0);
                let errors_rx = parts[3].parse::<u64>().unwrap_or(0);
                let dropped_rx = parts[4].parse::<u64>().unwrap_or(0);
                
                let bytes_tx = parts[9].parse::<u64>().unwrap_or(0);
                let packets_tx = parts[10].parse::<u64>().unwrap_or(0);
                let errors_tx = parts[11].parse::<u64>().unwrap_or(0);
                let dropped_tx = parts[12].parse::<u64>().unwrap_or(0);
                
                // Get interface capabilities
                let link_speed = Self::get_link_speed(name).unwrap_or(None);
                let duplex = Self::get_duplex(name).unwrap_or(None);
                let mtu = Self::get_mtu(name).unwrap_or(None);
                
                return Ok(NetworkMetrics {
                    bytes_tx,
                    bytes_rx,
                    packets_tx,
                    packets_rx,
                    errors_tx,
                    errors_rx,
                    dropped_tx,
                    dropped_rx,
                    speed_up: 0.0,    // Will be calculated over time
                    speed_down: 0.0,  // Will be calculated over time
                    packets_per_sec_tx: 0.0,
                    packets_per_sec_rx: 0.0,
                    link_speed,
                    duplex,
                    mtu,
                    uptime: None,     // Will be tracked by app
                    total_session_tx: 0,
                    total_session_rx: 0,
                });
            }
        }
        
        Ok(NetworkMetrics::default())
    }

    fn get_link_speed(name: &str) -> Result<Option<u32>> {
        // Try to read link speed from sysfs
        let speed_path = format!("/sys/class/net/{}/speed", name);
        match fs::read_to_string(&speed_path) {
            Ok(speed_str) => {
                if let Ok(speed) = speed_str.trim().parse::<u32>() {
                    Ok(Some(speed))
                } else {
                    Ok(None)
                }
            }
            Err(_) => Ok(None),
        }
    }

    fn get_duplex(name: &str) -> Result<Option<String>> {
        // Try to read duplex mode from sysfs
        let duplex_path = format!("/sys/class/net/{}/duplex", name);
        match fs::read_to_string(&duplex_path) {
            Ok(duplex_str) => {
                let duplex = duplex_str.trim().to_string();
                if !duplex.is_empty() && duplex != "unknown" {
                    Ok(Some(duplex))
                } else {
                    Ok(None)
                }
            }
            Err(_) => Ok(None),
        }
    }

    fn get_mtu(name: &str) -> Result<Option<u32>> {
        // Try to read MTU from sysfs
        let mtu_path = format!("/sys/class/net/{}/mtu", name);
        match fs::read_to_string(&mtu_path) {
            Ok(mtu_str) => {
                if let Ok(mtu) = mtu_str.trim().parse::<u32>() {
                    Ok(Some(mtu))
                } else {
                    Ok(None)
                }
            }
            Err(_) => Ok(None),
        }
    }
}

pub struct NetworkMonitor {
    previous_metrics: HashMap<String, NetworkMetrics>,
    last_update: std::time::Instant,
}

impl NetworkMonitor {
    pub fn new() -> Self {
        Self {
            previous_metrics: HashMap::new(),
            last_update: std::time::Instant::now(),
        }
    }

    pub fn update_speeds(&mut self, interfaces: &mut [NetworkInterface]) {
        let now = std::time::Instant::now();
        let time_diff = now.duration_since(self.last_update).as_secs_f64();
        
        if time_diff < 0.1 {
            return; // Too frequent updates
        }

        for interface in interfaces.iter_mut() {
            if let Some(prev_metrics) = self.previous_metrics.get(&interface.name) {
                // Calculate byte differences
                let bytes_tx_diff = interface.metrics.bytes_tx.saturating_sub(prev_metrics.bytes_tx);
                let bytes_rx_diff = interface.metrics.bytes_rx.saturating_sub(prev_metrics.bytes_rx);
                let packets_tx_diff = interface.metrics.packets_tx.saturating_sub(prev_metrics.packets_tx);
                let packets_rx_diff = interface.metrics.packets_rx.saturating_sub(prev_metrics.packets_rx);
                
                // Calculate speeds in KB/s and packets/s
                interface.metrics.speed_up = (bytes_tx_diff as f64) / time_diff / 1024.0;
                interface.metrics.speed_down = (bytes_rx_diff as f64) / time_diff / 1024.0;
                interface.metrics.packets_per_sec_tx = (packets_tx_diff as f64) / time_diff;
                interface.metrics.packets_per_sec_rx = (packets_rx_diff as f64) / time_diff;
            }
            
            // Store current metrics for next calculation
            self.previous_metrics.insert(interface.name.clone(), interface.metrics.clone());
        }
        
        self.last_update = now;
    }
}