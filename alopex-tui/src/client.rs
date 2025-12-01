/*!
 * ALOPEX Daemon Client
 * JSON IPC communication with alopexd
 */

use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::net::UnixStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Request {
    GetInterfaces,
    ConnectInterface { name: String },
    DisconnectInterface { name: String },
    ConfigureInterface { name: String, config: InterfaceConfig },
    GetMetrics { name: String },
}

#[derive(Debug, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum Response {
    InterfaceList { interfaces: Vec<NetworkInterface> },
    Success { message: String },
    Error { message: String },
    Metrics { metrics: NetworkMetrics },
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NetworkInterface {
    pub name: String,
    pub interface_type: String,
    pub status: String,
    pub config: InterfaceConfig,
    pub metrics: NetworkMetrics,
}

#[derive(Debug, Serialize, Deserialize)]
pub enum InterfaceConfig {
    Ethernet {
        dhcp: bool,
        ip: Option<String>,
        gateway: Option<String>,
        dns: Vec<String>,
    },
    WiFi {
        ssid: String,
        security: String,
    },
}

#[derive(Debug, Serialize, Deserialize, Default)]
pub struct NetworkMetrics {
    pub bytes_tx: u64,
    pub bytes_rx: u64,
    pub speed_up: f64,
    pub speed_down: f64,
    pub link_speed: Option<u32>,
}

pub struct AlopexClient {
    socket_path: String,
}

impl AlopexClient {
    pub fn new(socket_path: String) -> Self {
        Self { socket_path }
    }

    pub async fn send_request(&self, request: Request) -> Result<Response> {
        // For development, return mock responses
        match request {
            Request::GetInterfaces => Ok(Response::InterfaceList {
                interfaces: vec![
                    NetworkInterface {
                        name: "eth0".to_string(),
                        interface_type: "Ethernet".to_string(),
                        status: "Connected".to_string(),
                        config: InterfaceConfig::Ethernet {
                            dhcp: true,
                            ip: Some("192.168.1.100".to_string()),
                            gateway: Some("192.168.1.1".to_string()),
                            dns: vec!["1.1.1.1".to_string()],
                        },
                        metrics: NetworkMetrics {
                            link_speed: Some(1000),
                            ..Default::default()
                        },
                    },
                    NetworkInterface {
                        name: "wlan0".to_string(),
                        interface_type: "WiFi".to_string(),
                        status: "Disconnected".to_string(),
                        config: InterfaceConfig::WiFi {
                            ssid: "".to_string(),
                            security: "None".to_string(),
                        },
                        metrics: NetworkMetrics::default(),
                    },
                ]
            }),
            _ => Ok(Response::Success { 
                message: "Mock response".to_string() 
            }),
        }
    }

    async fn _real_send_request(&self, request: Request) -> Result<Response> {
        let mut stream = UnixStream::connect(&self.socket_path).await?;
        
        let request_json = serde_json::to_string(&request)?;
        stream.write_all(request_json.as_bytes()).await?;
        stream.write_all(b"\n").await?;

        let mut buffer = Vec::new();
        stream.read_to_end(&mut buffer).await?;
        
        let response_str = String::from_utf8(buffer)?;
        let response: Response = serde_json::from_str(&response_str)?;
        
        Ok(response)
    }
}