/*!
 * IPC Server for ALOPEX Daemon
 * JSON protocol over Unix socket
 */

use anyhow::Result;
use tokio::net::{UnixListener, UnixStream};
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use serde_json;

use crate::network::NetworkManager;
use crate::bluetooth::BluetoothManager;

pub struct IpcServer {
    listener: UnixListener,
    network_manager: NetworkManager,
    bluetooth_manager: BluetoothManager,
}

impl IpcServer {
    pub fn new(
        listener: UnixListener,
        network_manager: NetworkManager,
        bluetooth_manager: BluetoothManager,
    ) -> Self {
        Self {
            listener,
            network_manager,
            bluetooth_manager,
        }
    }

    pub async fn run(self) -> Result<()> {
        tracing::info!("IPC server listening for connections...");

        loop {
            match self.listener.accept().await {
                Ok((stream, _)) => {
                    tracing::debug!("New client connected");
                    let network_manager = &self.network_manager;
                    let bluetooth_manager = &self.bluetooth_manager;
                    
                    tokio::spawn(async move {
                        if let Err(e) = handle_client(stream, network_manager, bluetooth_manager).await {
                            tracing::error!("Client error: {}", e);
                        }
                    });
                }
                Err(e) => {
                    tracing::error!("Failed to accept connection: {}", e);
                }
            }
        }
    }
}

async fn handle_client(
    stream: UnixStream,
    _network_manager: &NetworkManager,
    _bluetooth_manager: &BluetoothManager,
) -> Result<()> {
    let mut reader = BufReader::new(&stream);
    let mut line = String::new();

    while reader.read_line(&mut line).await? > 0 {
        let request = line.trim();
        tracing::debug!("Received request: {}", request);

        // TODO: Parse JSON request and handle it
        let response = r#"{"type":"Success","message":"Not implemented yet"}"#;
        
        let mut stream = stream.try_clone()?;
        stream.write_all(response.as_bytes()).await?;
        stream.write_all(b"\n").await?;

        line.clear();
    }

    Ok(())
}