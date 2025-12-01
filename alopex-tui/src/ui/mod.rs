/*!
 * ALOPEX TUI Interface
 * Conservative, professional design with Telemetry Hub
 */

use ratatui::{
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, Paragraph},
    Frame,
};

use crate::app::{App, FocusedPanel};

// Conservative color palette
const BLUE: Color = Color::Rgb(100, 149, 237);
const GRAY: Color = Color::Rgb(128, 128, 128);
const WHITE: Color = Color::Rgb(255, 255, 255);
const GREEN: Color = Color::Rgb(34, 139, 34);
const RED: Color = Color::Rgb(220, 20, 60);

pub fn render_ui(f: &mut Frame, app: &App) {
    let chunks = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(25),  // Interfaces panel
            Constraint::Percentage(40),  // Network management  
            Constraint::Percentage(35),  // Telemetry Hub
        ])
        .split(f.area());

    render_interfaces_panel(f, chunks[0], app);
    render_management_panel(f, chunks[1], app);
    render_telemetry_hub(f, chunks[2], app);
}

fn render_interfaces_panel(f: &mut Frame, area: Rect, app: &App) {
    let border_style = if matches!(app.focused_panel, FocusedPanel::Interfaces) {
        Style::default().fg(BLUE)
    } else {
        Style::default().fg(GRAY)
    };

    let mut items = Vec::new();
    let mut current_type = "";
    
    for (i, interface) in app.interfaces.iter().enumerate() {
        // Add type header if this is a new interface type
        if interface.interface_type != current_type {
            if !items.is_empty() {
                // Add spacing between groups
                items.push(ListItem::new(Line::from("")));
            }
            items.push(ListItem::new(Line::from(vec![
                Span::styled(format!("━ {} ━", interface.interface_type), 
                           Style::default().fg(BLUE).add_modifier(Modifier::BOLD))
            ])));
            current_type = &interface.interface_type;
        }

        let prefix = if i == app.selected_interface { "▶ " } else { "  " };
        let status_indicator = match interface.status.as_str() {
            "Connected" => "●",
            "Connecting" => "◐", 
            _ => "○",
        };
        let status_color = match interface.status.as_str() {
            "Connected" => GREEN,
            "Connecting" => BLUE,
            _ => GRAY,
        };

        let content = Line::from(vec![
            Span::raw(prefix),
            Span::styled(status_indicator, Style::default().fg(status_color)),
            Span::raw(" "),
            Span::styled(&interface.name, Style::default().fg(WHITE)),
        ]);

        let item = if i == app.selected_interface {
            ListItem::new(content).style(Style::default().bg(BLUE).fg(WHITE))
        } else {
            ListItem::new(content)
        };
        items.push(item);
    }

    let list = List::new(items)
        .block(Block::default()
            .borders(Borders::ALL)
            .title("Network Interfaces")
            .border_style(border_style));

    f.render_widget(list, area);
}

fn render_management_panel(f: &mut Frame, area: Rect, app: &App) {
    let border_style = if matches!(app.focused_panel, FocusedPanel::Management) {
        Style::default().fg(BLUE)
    } else {
        Style::default().fg(GRAY)
    };

    if let Some(interface) = app.get_selected_interface() {
        let content = match interface.interface_type.as_str() {
            "Ethernet" => render_ethernet_management(interface),
            "WiFi" => render_wifi_management(interface),
            _ => vec![Line::from("Select an interface")],
        };

        let paragraph = Paragraph::new(content)
            .block(Block::default()
                .borders(Borders::ALL)
                .title("Network Management")
                .border_style(border_style))
            .alignment(Alignment::Left);

        f.render_widget(paragraph, area);
    } else {
        let paragraph = Paragraph::new("No interfaces available")
            .block(Block::default()
                .borders(Borders::ALL)
                .title("Network Management")
                .border_style(border_style))
            .alignment(Alignment::Center);

        f.render_widget(paragraph, area);
    }
}

fn render_ethernet_management(interface: &crate::app::NetworkInterface) -> Vec<Line> {
    let status_color = match interface.status.as_str() {
        "Connected" => GREEN,
        "Connecting" => BLUE,
        _ => RED,
    };

    vec![
        Line::from(vec![
            Span::styled(&interface.name, Style::default().fg(WHITE).add_modifier(Modifier::BOLD)),
            Span::styled(": Gigabit Link", Style::default().fg(GRAY)),
        ]),
        Line::from(""),
        Line::from(vec![
            Span::styled("Status: ", Style::default().fg(GRAY)),
            Span::styled(&interface.status, Style::default().fg(status_color)),
        ]),
        Line::from(vec![
            Span::styled("Mode: ", Style::default().fg(GRAY)),
            Span::styled("DHCP Auto", Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("IP: ", Style::default().fg(GRAY)),
            Span::styled(
                interface.ip.as_deref().unwrap_or("None"), 
                Style::default().fg(WHITE)
            ),
        ]),
        Line::from(vec![
            Span::styled("Gateway: ", Style::default().fg(GRAY)),
            Span::styled(
                interface.gateway.as_deref().unwrap_or("None"), 
                Style::default().fg(WHITE)
            ),
        ]),
        Line::from(""),
        Line::from("Static Override:"),
        Line::from("[ ] Manual IP Config"),
        Line::from(""),
        Line::from("[Enter] Connect/Disconnect"),
        Line::from("[c] Configure"),
    ]
}

fn render_wifi_management(interface: &crate::app::NetworkInterface) -> Vec<Line> {
    vec![
        Line::from(vec![
            Span::styled(&interface.name, Style::default().fg(WHITE).add_modifier(Modifier::BOLD)),
            Span::styled(": WiFi Interface", Style::default().fg(GRAY)),
        ]),
        Line::from(""),
        Line::from("WiFi management not implemented yet"),
        Line::from(""),
        Line::from("[s] Scan Networks"),
        Line::from("[c] Connect"),
    ]
}

fn render_telemetry_hub(f: &mut Frame, area: Rect, app: &App) {
    let border_style = if matches!(app.focused_panel, FocusedPanel::Telemetry) {
        Style::default().fg(BLUE)
    } else {
        Style::default().fg(GRAY)
    };

    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Min(6),          // Traffic graph (compact)
            Constraint::Min(5),          // Addressing (compact)
            Constraint::Min(6),          // Session stats (compact)
        ])
        .split(area);

    // Telemetry Hub container
    let hub_block = Block::default()
        .borders(Borders::ALL)
        .title("Telemetry Hub")
        .border_style(border_style);

    f.render_widget(hub_block, area);

    if app.telemetry_active {
        render_traffic_section(f, chunks[0], app);
        render_addressing_section(f, chunks[1], app);
        render_session_section(f, chunks[2], app);
    } else {
        let inactive = Paragraph::new("No Active Connection")
            .style(Style::default().fg(GRAY))
            .alignment(Alignment::Center);
        let center_area = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Percentage(40),
                Constraint::Percentage(20),
                Constraint::Percentage(40),
            ])
            .split(area)[1];
        f.render_widget(inactive, center_area);
    }
}

fn render_traffic_section(f: &mut Frame, area: Rect, app: &App) {
    let interface = app.get_selected_interface().unwrap();
    
    // Create mini traffic graph using traffic history
    let sparkline = create_traffic_sparkline(&app.traffic_history);
    
    let download_sparkline = create_download_sparkline(&app.traffic_history);
    let content = vec![
        Line::from(vec![
            Span::styled("↑ ", Style::default().fg(GREEN)),
            Span::styled(&sparkline, Style::default().fg(GREEN)),
            Span::raw(" "),
            Span::styled(format!("{:.1}K", interface.metrics.speed_up), Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("↓ ", Style::default().fg(BLUE)),
            Span::styled(&download_sparkline, Style::default().fg(BLUE)),
            Span::raw(" "),
            Span::styled(format!("{:.1}K", interface.metrics.speed_down), Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("Pkt ", Style::default().fg(GRAY)),
            Span::styled(format!("{:.0}/s ↑{:.0}", interface.metrics.packets_per_sec_tx, interface.metrics.packets_per_sec_rx), Style::default().fg(WHITE)),
        ]),
    ];

    let traffic_block = Paragraph::new(content)
        .block(Block::default().borders(Borders::TOP))
        .alignment(Alignment::Left);
    
    f.render_widget(traffic_block, area);
}

fn render_addressing_section(f: &mut Frame, area: Rect, app: &App) {
    let interface = app.get_selected_interface().unwrap();
    
    let dns_fallback = "None".to_string();
    let content = vec![
        Line::from("Addressing"),
        Line::from(vec![
            Span::styled("Local: ", Style::default().fg(GRAY)),
            Span::styled(interface.ip.as_deref().unwrap_or("None"), Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("   GW: ", Style::default().fg(GRAY)),
            Span::styled(interface.gateway.as_deref().unwrap_or("None"), Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("  DNS: ", Style::default().fg(GRAY)),
            Span::styled(interface.dns.first().unwrap_or(&dns_fallback), Style::default().fg(WHITE)),
        ]),
    ];

    let addressing_block = Paragraph::new(content)
        .block(Block::default().borders(Borders::TOP))
        .alignment(Alignment::Left);
    
    f.render_widget(addressing_block, area);
}

fn render_session_section(f: &mut Frame, area: Rect, app: &App) {
    let interface = app.get_selected_interface().unwrap();
    
    let uptime = if let Some(duration) = interface.metrics.uptime {
        format!("{}h {}m", duration.as_secs() / 3600, (duration.as_secs() % 3600) / 60)
    } else {
        "N/A".to_string()
    };

    let duplex_info = match interface.metrics.duplex.as_deref() {
        Some(d) => format!("{}", d.to_uppercase()),
        None => "Unknown".to_string(),
    };

    let content = vec![
        Line::from("Session"),
        Line::from(vec![
            Span::styled("Uptime: ", Style::default().fg(GRAY)),
            Span::styled(uptime, Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("Link: ", Style::default().fg(GRAY)),
            Span::styled(
                format!("{}Mbps/{}", interface.metrics.link_speed.unwrap_or(0), duplex_info), 
                Style::default().fg(WHITE)
            ),
        ]),
        Line::from(vec![
            Span::styled("MTU: ", Style::default().fg(GRAY)),
            Span::styled(format!("{}", interface.metrics.mtu.unwrap_or(0)), Style::default().fg(WHITE)),
        ]),
        Line::from(vec![
            Span::styled("Errors: ", Style::default().fg(GRAY)),
            Span::styled(format!("↑{} ↓{}", interface.metrics.errors_tx, interface.metrics.errors_rx), 
                        if interface.metrics.errors_tx + interface.metrics.errors_rx > 0 { Style::default().fg(RED) } else { Style::default().fg(WHITE) }
            ),
        ]),
    ];

    let session_block = Paragraph::new(content)
        .block(Block::default().borders(Borders::TOP))
        .alignment(Alignment::Left);
    
    f.render_widget(session_block, area);
}

fn create_traffic_sparkline(history: &[(f64, f64)]) -> String {
    if history.is_empty() {
        return "▁▁▁▁▁▁▁▁".to_string();
    }

    let max_upload = history.iter().map(|(up, _)| *up).fold(0.0, f64::max);
    if max_upload == 0.0 {
        return "▁▁▁▁▁▁▁▁".to_string();
    }

    let chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
    history.iter()
        .map(|(up, _)| {
            let ratio = up / max_upload;
            let index = ((ratio * 7.0) as usize).min(7);
            chars[index]
        })
        .collect()
}

fn create_download_sparkline(history: &[(f64, f64)]) -> String {
    if history.is_empty() {
        return "▁▁▁▁▁▁▁▁".to_string();
    }

    let max_download = history.iter().map(|(_, down)| *down).fold(0.0, f64::max);
    if max_download == 0.0 {
        return "▁▁▁▁▁▁▁▁".to_string();
    }

    let chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█'];
    history.iter()
        .map(|(_, down)| {
            let ratio = down / max_download;
            let index = ((ratio * 7.0) as usize).min(7);
            chars[index]
        })
        .collect()
}