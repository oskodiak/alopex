/*!
 * ALOPEX Network Management TUI
 * Professional network control with Telemetry Hub
 * Onyx Digital Intelligence Development LLC
 */

use anyhow::Result;
use clap::Parser;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use ratatui::{
    backend::CrosstermBackend,
    Terminal,
};
use std::io;
use tokio::time::{interval, Duration};

mod ui;
mod client;
mod app;
mod network;

use app::App;
use ui::render_ui;

#[derive(Parser)]
#[command(name = "alopex")]
#[command(about = "ALOPEX Network Management TUI")]
struct Cli {
    /// Daemon socket path
    #[arg(short, long, default_value = "/run/alopex/alopex.sock")]
    socket: String,

    /// Enable debug mode
    #[arg(short, long)]
    debug: bool,
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    
    // Initialize terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Initialize app
    let mut app = App::new(&cli.socket).await?;

    // Create ticker for UI updates
    let mut ticker = interval(Duration::from_millis(100));

    let result = loop {
        // Handle events
        if event::poll(Duration::from_millis(0))? {
            if let Event::Key(key) = event::read()? {
                match key.code {
                    KeyCode::Char('q') => break Ok(()),
                    KeyCode::Up => app.previous_interface(),
                    KeyCode::Down => app.next_interface(),
                    KeyCode::Enter => app.toggle_connection().await?,
                    KeyCode::Tab => app.next_panel(),
                    KeyCode::Char('r') => app.refresh_data().await?,
                    _ => {}
                }
            }
        }

        // Update telemetry
        ticker.tick().await;
        app.update_metrics().await?;

        // Render UI
        terminal.draw(|f| render_ui(f, &app))?;
    };

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    result
}