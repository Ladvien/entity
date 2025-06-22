# src/client/chat_interface.py - ENHANCED VERSION WITH TTS PLAYBACK

"""
Enhanced terminal chat interface with TTS audio playback
"""

import logging
import asyncio
import subprocess
import platform
from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import print as rprint

from src.client.client import EntityAPIClient
from src.client.render import AgentResultRenderer


logger = logging.getLogger(__name__)


class AudioPlayer:
    """Cross-platform audio player for TTS files"""

    def __init__(self):
        self.system = platform.system().lower()
        self.player_command = self._detect_audio_player()

    def _detect_audio_player(self) -> Optional[str]:
        """Detect available audio player on the system"""

        # Audio players to try, in order of preference
        players = {
            "darwin": ["afplay", "ffplay", "vlc"],  # macOS
            "linux": ["aplay", "paplay", "ffplay", "vlc", "mpv"],  # Linux
            "windows": ["start", "ffplay", "vlc"],  # Windows
        }

        system_players = players.get(self.system, players["linux"])

        for player in system_players:
            if self._command_exists(player):
                logger.info(f"🔊 Detected audio player: {player}")
                return player

        logger.warning("⚠️ No audio player detected. Audio playback disabled.")
        return None

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists on the system"""
        try:
            if self.system == "windows":
                subprocess.run(
                    ["where", command],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            else:
                subprocess.run(
                    ["which", command],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            return True
        except subprocess.CalledProcessError:
            return False

    async def play_audio(self, audio_path: str) -> bool:
        """Play audio file asynchronously"""
        if not self.player_command:
            logger.warning("⚠️ No audio player available")
            return False

        if not Path(audio_path).exists():
            logger.warning(f"⚠️ Audio file not found: {audio_path}")
            return False

        try:
            logger.info(f"🔊 Playing audio: {audio_path}")

            # Prepare command based on player
            if self.player_command == "afplay":  # macOS
                cmd = ["afplay", audio_path]
            elif self.player_command == "aplay":  # Linux ALSA
                cmd = ["aplay", audio_path]
            elif self.player_command == "paplay":  # Linux PulseAudio
                cmd = ["paplay", audio_path]
            elif self.player_command == "ffplay":  # ffmpeg
                cmd = ["ffplay", "-nodisp", "-autoexit", audio_path]
            elif self.player_command == "vlc":  # VLC
                cmd = ["vlc", "--intf", "dummy", "--play-and-exit", audio_path]
            elif self.player_command == "mpv":  # mpv
                cmd = ["mpv", "--no-video", audio_path]
            elif self.player_command == "start":  # Windows
                cmd = ["start", "/wait", audio_path]
            else:
                cmd = [self.player_command, audio_path]

            # Run audio player
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            # Wait for playback to complete
            await process.wait()

            if process.returncode == 0:
                logger.debug("✅ Audio playback completed successfully")
                return True
            else:
                logger.warning(
                    f"⚠️ Audio playback failed with return code: {process.returncode}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ Audio playback error: {e}")
            return False


class ChatInterface:
    """Interactive terminal chat interface with TTS audio playback"""

    def __init__(self, client: EntityAPIClient, config: Dict[str, Any]):
        self.client = client
        self.config = config
        self.current_thread = "default"
        self.local_history = []
        self.console = Console()
        self.prompt = "[bold cyan]You:[/bold cyan] "
        self.audio_player = AudioPlayer()

        # TTS settings
        self.tts_enabled = config.get("tts_enabled", True)
        self.auto_play = config.get("auto_play_audio", True)
        self.audio_download_path = Path(
            config.get("audio_download_path", "./downloaded_audio")
        )
        self.audio_download_path.mkdir(exist_ok=True)

        if config.get("save_locally", True):
            self.history_path = Path(
                config.get("local_history_path", "./local_chat_history")
            )
            self.history_path.mkdir(parents=True, exist_ok=True)

    async def run(self):
        await self.start()

    async def start(self):
        await self._show_welcome()
        await self._chat_loop()

    async def _chat_loop(self):
        while True:
            try:
                user_input = self.console.input(self.prompt).strip()
                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit"}:
                    self.console.print("👋 Goodbye.", style="bold green")
                    break

                # Handle special commands
                if user_input.lower() in {"toggle audio", "toggle tts"}:
                    self.auto_play = not self.auto_play
                    status = "enabled" if self.auto_play else "disabled"
                    self.console.print(
                        f"🔊 Audio playback {status}", style="bold yellow"
                    )
                    continue

                if user_input.lower() in {"help", "commands"}:
                    self._show_commands()
                    continue

                # Send chat message
                agent_result = await self.client.chat(
                    user_input, thread_id=self.current_thread
                )

                # Render the response
                renderer = AgentResultRenderer(agent_result)

                if self.config.get("debug_mode", False):
                    self.console.print("[bold red]🐛 DEBUG MODE ACTIVE[/bold red]")
                    renderer.render_debug()
                elif (
                    self.config.get("show_react_steps", True)
                    and agent_result.react_steps
                ):
                    renderer.render()
                else:
                    renderer.render_simple()

                # 🎵 Handle TTS audio playback
                await self._handle_tts_audio(agent_result)

                # Save to local history
                if self.config.get("save_locally", True):
                    self.local_history.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "user_input": user_input,
                            "agent_output": agent_result.final_response,
                            "tools_used": agent_result.tools_used,
                            "memory_used": bool(agent_result.memory_context.strip()),
                            "react_steps_count": len(agent_result.react_steps or []),
                            "tts_enabled": getattr(agent_result, "tts_enabled", False),
                            "audio_file_id": getattr(
                                agent_result, "audio_file_id", None
                            ),
                        }
                    )
                print()

            except Exception as e:
                logger.exception("❌ Chat error")
                self.console.print(f"❌ Error: {e}", style="red")

    async def _handle_tts_audio(self, agent_result):
        """Handle TTS audio playback for agent responses"""

        # Check if TTS data is available in the result
        # The TTS data might be in different places depending on the API response format
        tts_enabled = getattr(agent_result, "tts_enabled", False)
        audio_file_id = getattr(agent_result, "audio_file_id", None)

        # Also check in metadata if available
        if hasattr(agent_result, "metadata") and isinstance(
            agent_result.metadata, dict
        ):
            tts_enabled = tts_enabled or agent_result.metadata.get("tts_enabled", False)
            audio_file_id = audio_file_id or agent_result.metadata.get("audio_file_id")

        if not self.tts_enabled or not self.auto_play:
            return

        if not tts_enabled:
            self.console.print("🔇 No audio available for this response", style="dim")
            return

        if not audio_file_id:
            self.console.print("⚠️ Audio file ID not found", style="yellow")
            return

        try:
            # Try to find the audio file locally first
            local_audio_path = await self._find_local_audio(audio_file_id)

            if local_audio_path:
                self.console.print(f"🎵 Playing audio...", style="green")
                success = await self.audio_player.play_audio(str(local_audio_path))

                if success:
                    self.console.print("✅ Audio playback completed", style="green")
                else:
                    self.console.print("❌ Audio playback failed", style="red")
            else:
                # Try to download from server
                downloaded_path = await self._download_audio(audio_file_id)

                if downloaded_path:
                    self.console.print(f"🎵 Playing downloaded audio...", style="green")
                    success = await self.audio_player.play_audio(str(downloaded_path))

                    if success:
                        self.console.print("✅ Audio playback completed", style="green")
                    else:
                        self.console.print("❌ Audio playback failed", style="red")
                else:
                    self.console.print(
                        "❌ Could not find or download audio file", style="red"
                    )

        except Exception as e:
            logger.error(f"❌ TTS audio handling error: {e}")
            self.console.print(f"❌ Audio error: {e}", style="red")

    async def _find_local_audio(self, audio_file_id: str) -> Optional[Path]:
        """Find audio file in local directories"""

        # Common audio file extensions
        extensions = [".wav", ".mp3", ".ogg", ".m4a"]

        # Directories to search
        search_dirs = [
            Path("./audio_output"),
            Path("./downloaded_audio"),
            self.audio_download_path,
        ]

        for directory in search_dirs:
            if not directory.exists():
                continue

            for ext in extensions:
                # Try exact filename
                file_path = directory / f"{audio_file_id}{ext}"
                if file_path.exists():
                    logger.info(f"📁 Found local audio: {file_path}")
                    return file_path

                # Try without extension (in case it's already included)
                file_path = directory / audio_file_id
                if file_path.exists():
                    logger.info(f"📁 Found local audio: {file_path}")
                    return file_path

        logger.debug(f"🔍 Local audio file not found: {audio_file_id}")
        return None

    async def _download_audio(self, audio_file_id: str) -> Optional[Path]:
        """Download audio file from server"""

        try:
            # Try to download from the TTS server
            server_url = self.config.get("tts_server_url", "http://192.168.1.110:8888")
            audio_url = f"{server_url}/audio/{audio_file_id}"

            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(audio_url)
                response.raise_for_status()

                # Determine file extension from content type
                content_type = response.headers.get("content-type", "")
                if "wav" in content_type:
                    ext = ".wav"
                elif "mp3" in content_type:
                    ext = ".mp3"
                elif "ogg" in content_type:
                    ext = ".ogg"
                else:
                    ext = ".wav"  # Default

                # Save file
                download_path = self.audio_download_path / f"{audio_file_id}{ext}"
                with open(download_path, "wb") as f:
                    f.write(response.content)

                logger.info(f"📥 Downloaded audio: {download_path}")
                return download_path

        except Exception as e:
            logger.error(f"❌ Audio download failed: {e}")
            return None

    def _show_commands(self):
        """Show available commands"""

        commands_table = Table(title="Available Commands", show_header=True)
        commands_table.add_column("Command", style="bold yellow")
        commands_table.add_column("Description")

        commands_table.add_row("exit, quit", "Exit chat")
        commands_table.add_row("help, commands", "Show this help message")
        commands_table.add_row("toggle audio", "Enable/disable audio playback")
        commands_table.add_row("toggle tts", "Same as toggle audio")

        self.console.print(commands_table)

    async def _show_welcome(self):
        self.console.clear()
        welcome_text = """[bold cyan]🤖 Entity Agent CLI Client with TTS[/bold cyan]
[dim]Connected to Entity Agent with Audio Playback Support[/dim]"""
        self.console.print(Panel(welcome_text, title="Welcome", border_style="cyan"))

        health = await self.client.health_check()
        if health.get("status") == "healthy":
            self.console.print(
                f"✅ Connected to service at [green]{self.client.base_url}[/green]"
            )
            features = health.get("features", {})
            if features.get("vector_memory"):
                self.console.print("📊 Vector Memory: [green]Enabled[/green]")
            if features.get("postgresql"):
                self.console.print("🐘 PostgreSQL: [green]Connected[/green]")
            if features.get("tts_enabled"):
                self.console.print("🎵 TTS Audio: [green]Available[/green]")
        else:
            self.console.print(f"⚠️  Service may be unavailable", style="yellow")

        # Test audio player
        if self.audio_player.player_command:
            self.console.print(
                f"🔊 Audio Player: [green]{self.audio_player.player_command}[/green]"
            )
        else:
            self.console.print("🔇 Audio Player: [red]Not Available[/red]")
            self.auto_play = False

        audio_status = "enabled" if self.auto_play else "disabled"
        self.console.print(
            f"🎵 Auto-play Audio: [{'green' if self.auto_play else 'yellow'}]{audio_status}[/{'green' if self.auto_play else 'yellow'}]"
        )

        try:
            memory_stats = await self.client.get_memory_stats()
            if memory_stats:
                self.console.print(f"\n💾 Memory Stats:")
                self.console.print(
                    f"   Total Memories: [cyan]{memory_stats.get('total_memories', 0)}[/cyan]"
                )
                self.console.print(
                    f"   Conversations: [cyan]{memory_stats.get('total_conversations', 0)}[/cyan]"
                )
                self.console.print(
                    f"   Embedding Model: [dim]{memory_stats.get('embedding_model', 'unknown')}[/dim]"
                )
        except Exception as e:
            logger.warning(f"Could not fetch memory stats: {e}")

        tools = await self.client.list_tools()
        if tools:
            self.console.print(f"\n🛠️  Available tools: [cyan]{', '.join(tools)}[/cyan]")

        self._show_commands()

        self.console.print(f"\n📝 Current thread: [cyan]{self.current_thread}[/cyan]")
        self.console.print("─" * 60 + "\n")
