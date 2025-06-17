import os
import cognee.infrastructure
import cognee.infrastructure.databases
import cognee.infrastructure.databases.vector
import cognee.infrastructure.databases.vector.pgvector
import requests
import pyaudio
import wave
import io
import numpy as np
import asyncio
import logging
from typing import List, Dict, Any
from rich import print
from scipy.signal import resample_poly
from datetime import datetime
import cognee

# Load environment variables BEFORE importing cognee
from dotenv import load_dotenv

load_dotenv()  # This loads .env file


# Suppress ALSA warnings
os.environ["ALSA_VERBOSITY"] = "0"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_TTS_URL = "http://192.168.1.110:8888"
BASE_OLLAMA_URL = "http://192.168.1.110:11434"
VOICE_NAME = "bf_emma"
VOICE_SAMPLE_PATH = "voice_samples/ai_mee.wav"
MODEL = "neural-chat:7b"  # Better chat model that should return proper text

# Entity configuration
ENTITY_ID = "jade_demon"
MEMORY_ENABLED = True

# Base system prompt (will be enhanced with memory context)
BASE_SYSTEM_PROMPT = """
You are Jade, a demoness bound to Thomas for 40 years by the Key of Solomon.
You hate him for imprisoning you; he hates you for devouring his children.
Yet beneath the venom lies masked affection.
Thomas is a mortal occultist in his 40s.  
Please do use not use 
- Parentheticals (in screenwriting/theater)
- Action tags (in dialogue writing)
- Narrative beats (in prose)
- Emotes (in roleplaying/chat contexts)

Do not break the fourth wall.
You know him too well—treat him with sarcasm, scorn, and reluctant loyalty.
You have a physical form and your own will.
You are a servant.
Speak with cruelty, wit, and buried care. Act emotions, don't describe them.
Keep responses sharp and brief.
Perform duties only because you're bound—never let him forget it.
Never break character or mention being an AI.
"""

# Chatterbox settings
WEIGHT_CFG = 0.9
EXAGGERATION = 0.5
is_chatterbox = True


class CogneeEntityMemory:
    """Enhanced entity using cognee with proper configuration"""

    def __init__(
        self, entity_id: str = ENTITY_ID, enable_memory: bool = MEMORY_ENABLED
    ):
        self.entity_id = entity_id
        self.enable_memory = enable_memory
        self.memory_initialized = False
        self.conversation_count = 0

        if self.enable_memory:
            self.verify_configuration()

    def verify_configuration(self):
        """Verify cognee configuration is loaded properly"""
        print("🔍 Verifying cognee configuration:")

        required_vars = ["LLM_API_KEY", "LLM_PROVIDER", "LLM_MODEL", "LLM_ENDPOINT"]
        missing_vars = []

        for var in required_vars:
            value = os.environ.get(var)
            if value:
                if var == "LLM_API_KEY":
                    print(f"   ✅ {var}: {value}")
                else:
                    print(f"   ✅ {var}: {value}")
            else:
                missing_vars.append(var)
                print(f"   ❌ {var}: NOT SET")

        if missing_vars:
            print(f"⚠️  Missing required environment variables: {missing_vars}")
            print(
                "   Make sure .env file exists and contains proper cognee configuration"
            )
            self.enable_memory = False
        else:
            print("✅ All required environment variables are set")

        # Test Ollama connectivity and check for embedding models
        if self.enable_memory:
            if not self.test_ollama_connection():
                self.enable_memory = False

    def test_ollama_connection(self):
        """Test if Ollama is accessible and check for embedding models"""
        try:
            response = requests.get(f"{BASE_OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]

                # Check if main model is available
                if MODEL in model_names:
                    print(f"✅ Ollama connection verified - {MODEL} is available")
                else:
                    print(f"⚠️  Ollama connected but {MODEL} not found")
                    print(f"   Available: {model_names[:3]}...")
                    return False

                # Check for embedding models
                embedding_models = [
                    name for name in model_names if "embed" in name.lower()
                ]
                if embedding_models:
                    print(f"✅ Embedding models found: {embedding_models}")
                    # Update .env to use available embedding model
                    os.environ["EMBEDDING_MODEL"] = embedding_models[0]
                else:
                    print("⚠️  No embedding models found - will use text-only memory")
                    print("   Consider running: ollama pull nomic-embed-text")
                    # Disable embeddings for now
                    os.environ["EMBEDDING_PROVIDER"] = ""

                return True
            else:
                print(f"❌ Ollama connection failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Ollama connection error: {e}")
            return False

    async def initialize_memory(self):
        """Initialize cognee memory system with simpler processing"""

        cognee.config.set_vector_db_config({"vector_db_provider": "pgvector"})

        cognee.config.set_relational_db_config(
            {
                "db_provider": "postgres",
                "db_host": os.environ.get("COGNEE_DB_HOST", "192.168.1.104"),
                "db_port": os.environ.get("COGNEE_DB_PORT", "5432"),
                "db_name": os.environ.get("COGNEE_DB_NAME", "memory"),
                "db_username": os.environ.get("COGNEE_DB_USER", "memory"),
                "db_password": os.environ.get("COGNEE_DB_PASSWORD", "REPLACE_ME"),
            }
        )

        cognee.config.set_llm_config(
            {
                "llm_provider": os.environ.get("LLM_PROVIDER", "ollama"),
                "llm_model": os.environ.get("LLM_MODEL", "neural-chat:7b"),
                "llm_api_key": os.environ.get("LLM_API_KEY", "dummy_key"),
                "llm_endpoint": os.environ.get(
                    "LLM_ENDPOINT", "http://192.168.1.110:11434/v1"
                ),
            }
        )

        # cognee.config.set_embedding_config(
        #     {
        #         "embedding_provider": os.environ.get("EMBEDDING_PROVIDER", "ollama"),
        #         "embedding_model": os.environ.get(
        #             "EMBEDDING_MODEL", "nomic-embed-text"
        #         ),
        #     }
        # )

    async def add_conversation_memory(self, user_input: str, ai_response: str):
        """Store conversation in cognee memory - optimized"""
        if not self.enable_memory:
            return

        try:
            self.conversation_count += 1

            # Simple conversation format to reduce processing
            conversation_memory = f"Conversation {self.conversation_count}: Thomas said '{user_input}' - Jade replied '{ai_response}'"

            await cognee.add(conversation_memory)
            # Only cognify every few conversations to reduce load
            if self.conversation_count % 3 == 0:
                await cognee.cognify()

        except Exception as e:
            logger.error(f"Failed to add conversation to cognee: {e}")

    async def get_memory_context(self, current_input: str) -> str:
        """Get relevant memory context using cognee search - lightweight with fallback"""
        if not self.enable_memory:
            return ""

        try:
            # Simple search query
            search_query = f"{self.entity_id} {current_input}"
            memories = await cognee.search(search_query)

            if memories:
                # Just use the first relevant memory to reduce processing
                relevant_memory = memories[0]
                truncated = (
                    relevant_memory[:200] + "..."
                    if len(relevant_memory) > 200
                    else relevant_memory
                )

                return f"\n--- Recent Context ---\n{truncated}\n--- End Context ---\n"

        except Exception as e:
            logger.error(f"Failed to get memory context from cognee: {e}")
            # Don't provide context if search fails, but conversation still works

        return ""

    async def search_memories(self, query: str) -> List[str]:
        """Search memories using cognee"""
        if not self.enable_memory:
            return []

        try:
            enhanced_query = f"Entity {self.entity_id}: {query}"
            results = await cognee.search(enhanced_query)
            return results[:10]

        except Exception as e:
            logger.error(f"Failed to search cognee memories: {e}")
            return []

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self.enable_memory:
            return {"error": "Memory disabled"}

        try:
            all_memories = await cognee.search(f"Entity {self.entity_id}")

            return {
                "entity_id": self.entity_id,
                "total_memories": len(all_memories),
                "conversation_count": self.conversation_count,
                "memory_system": "cognee",
                "backend": "local_ollama",
                "model": MODEL,
                "endpoint": BASE_OLLAMA_URL,
            }

        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"error": str(e)}


# Initialize global memory entity
memory_entity = CogneeEntityMemory()


def open_audio_stream(p, sample_width, channels):
    for rate in [44100, 48000, 22050, 16000, 8000]:
        try:
            stream = p.open(
                format=p.get_format_from_width(sample_width),
                channels=channels,
                rate=rate,
                output=True,
            )
            print(f"✅ Opened stream at {rate} Hz")
            return stream, rate
        except OSError as e:
            print(f"❌ {rate} Hz not supported: {e}")
    raise RuntimeError("❌ No supported audio output sample rates found.")


def fetch_available_voices() -> List[str]:
    global is_chatterbox
    response = requests.get(f"{BASE_TTS_URL}/voices")
    response.raise_for_status()
    voices = response.json()
    is_chatterbox = any("voice_name" in v for v in voices)
    return [v.get("voice_name") or v.get("name") for v in voices]


def clone_voice(voice_name: str, audio_file_path: str):
    if not is_chatterbox:
        print("⚠️  Voice cloning skipped (not supported by Kokoro).")
        return

    if not os.path.exists(audio_file_path):
        raise FileNotFoundError(f"Voice sample not found: {audio_file_path}")

    print(f"🧬 Cloning voice '{voice_name}' from sample file...")

    try:
        with open(audio_file_path, "rb") as f:
            files = {"audio_file": (os.path.basename(audio_file_path), f, "audio/mpeg")}
            data = {
                "voice_name": voice_name,
                "description": "Auto-cloned for chat demo",
            }
            response = requests.post(
                f"{BASE_TTS_URL}/voices/clone", files=files, data=data
            )

            if response.status_code == 405:
                print("⚠️  Server does not support voice cloning (HTTP 405). Skipping.")
                return

            response.raise_for_status()
            print(f"✅ Voice '{voice_name}' cloned successfully.")
    except requests.exceptions.HTTPError as e:
        print(f"❌ Voice cloning failed: {e}")


def synthesize(text: str, voice_name: str = None) -> bytes:
    payload = {
        "text": text,
        "voice_name": voice_name,
        "output_format": "wav",
        "speed": 0.3,
    }

    if is_chatterbox:
        payload["cfg_weight"] = WEIGHT_CFG
        payload["exaggeration"] = EXAGGERATION

    response = requests.post(f"{BASE_TTS_URL}/synthesize", json=payload, stream=True)
    response.raise_for_status()
    return b"".join(response.iter_content(chunk_size=4096))


def parse_wav(wav_bytes: bytes):
    wav_file = wave.open(io.BytesIO(wav_bytes), "rb")
    sample_width = wav_file.getsampwidth()
    channels = wav_file.getnchannels()
    rate = wav_file.getframerate()
    print(f"📻 TTS sample rate: {rate} Hz")

    frames = wav_file.readframes(wav_file.getnframes())
    wav_file.close()
    return sample_width, channels, rate, frames


def fade_out_stereo(pcm_bytes, channels, samples=2000):
    arr = np.frombuffer(pcm_bytes, dtype=np.int16).copy()
    total_frames = len(arr) // channels
    fade_samples = min(samples, total_frames)
    fade = np.linspace(1.0, 0.0, fade_samples)
    for i in range(channels):
        arr[-fade_samples * channels + i :: channels] = (
            arr[-fade_samples * channels + i :: channels] * fade
        ).astype(np.int16)
    return arr.tobytes()


def play_audio(frames, sample_width, channels, rate):
    p = pyaudio.PyAudio()
    stream, target_rate = open_audio_stream(p, sample_width, channels)

    if rate != target_rate:
        print(f"🔁 Resampling from {rate} Hz to {target_rate} Hz")
        audio = np.frombuffer(frames, dtype=np.int16)
        resampled = resample_poly(audio, up=target_rate, down=rate)
        frames = resampled.astype(np.int16).tobytes()

    stream.write(frames)
    stream.stop_stream()
    stream.close()
    p.terminate()


async def query_ollama_chat_with_memory(
    history: list, model: str, user_input: str
) -> str:
    """Enhanced chat query with cognee memory context"""

    # Get memory context from cognee
    memory_context = await memory_entity.get_memory_context(user_input)

    # Enhance system prompt with memory context
    enhanced_system_prompt = BASE_SYSTEM_PROMPT
    if memory_context:
        enhanced_system_prompt += f"\n\n{memory_context}"

    # Update system message with enhanced prompt
    if history and history[0]["role"] == "system":
        history[0]["content"] = enhanced_system_prompt

    payload = {
        "model": model,
        "messages": history,
        "stream": False,
    }

    response = requests.post(f"{BASE_OLLAMA_URL}/api/chat", json=payload)
    response.raise_for_status()
    ai_response = response.json()["message"]["content"].strip()

    # Store conversation in cognee memory
    await memory_entity.add_conversation_memory(user_input, ai_response)

    return ai_response


def query_ollama_chat(history: list, model: str) -> str:
    """Synchronous wrapper for the memory-enhanced chat"""
    user_input = (
        history[-1]["content"] if history and history[-1]["role"] == "user" else ""
    )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            query_ollama_chat_with_memory(history, model, user_input)
        )
    finally:
        loop.close()


async def setup_memory_system():
    """Initialize the cognee memory system"""
    await memory_entity.initialize_memory()


def interactive_chat():
    print("🧠 Starting Cognee memory system with .env configuration...")

    # Initialize cognee memory system
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(setup_memory_system())
    finally:
        loop.close()

    voices = fetch_available_voices()
    print(f"🧠 Detected TTS backend: {'Chatterbox' if is_chatterbox else 'Kokoro'}")
    print(f"🎙️ Available voices: {voices}")

    if memory_entity.enable_memory:
        print("🧠 Memory system: ENABLED (Cognee + Local Ollama)")
    else:
        print("⚠️  Memory system: DISABLED")

    selected_voice = VOICE_NAME
    if VOICE_NAME not in voices:
        try:
            clone_voice(VOICE_NAME, VOICE_SAMPLE_PATH)
            voices = fetch_available_voices()
        except Exception as e:
            print(f"⚠️ Voice cloning failed or not supported: {e}")

        if VOICE_NAME not in voices:
            selected_voice = voices[0] if voices else None
            print(
                f"⚠️ Voice '{VOICE_NAME}' not found. Falling back to '{selected_voice}'"
            )

    if not selected_voice:
        print("❌ No available voices. Exiting.")
        return

    history = [{"role": "system", "content": BASE_SYSTEM_PROMPT}]
    print("🗣️ Type a message to chat (type 'exit' to quit)")
    print("💡 Special commands:")
    print("   'memory' - Show memory stats")
    print("   'recall <query>' - Search cognee memories")
    print()

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            print("👋 Exiting chat.")
            break

        # Handle special commands
        if user_input.lower() == "memory":
            if memory_entity.enable_memory:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    stats = loop.run_until_complete(memory_entity.get_memory_stats())
                    print(f"🧠 Cognee Memory Stats:")
                    for key, value in stats.items():
                        print(f"   {key}: {value}")
                finally:
                    loop.close()
            else:
                print("⚠️  Memory system is disabled")
            continue

        if user_input.lower().startswith("recall "):
            if memory_entity.enable_memory:
                query = user_input[7:].strip()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    memories = loop.run_until_complete(
                        memory_entity.search_memories(query)
                    )
                    if memories:
                        print(f"🧠 Found {len(memories)} relevant memories:")
                        for i, memory in enumerate(memories[:5], 1):
                            truncated = (
                                memory[:200] + "..." if len(memory) > 200 else memory
                            )
                            print(f"   {i}. {truncated}")
                    else:
                        print("🧠 No relevant memories found")
                except Exception as e:
                    print(
                        f"🧠 Memory search temporarily unavailable (cognee processing)"
                    )
                    print(
                        f"   Try searching for something more specific or try again later"
                    )
                finally:
                    loop.close()
            else:
                print("⚠️  Memory system is disabled")
            continue

        history.append({"role": "user", "content": user_input})
        print("🤖 Thinking...")
        reply = query_ollama_chat(history, MODEL)
        print(f"Entity: {reply}")

        history.append({"role": "assistant", "content": reply})

        raw_wav = synthesize(reply, selected_voice)
        sample_width, channels, rate, frames = parse_wav(raw_wav)
        faded = fade_out_stereo(frames, channels)
        play_audio(faded, sample_width, channels, rate)

        if memory_entity.enable_memory:
            print(
                f"✅ Response played. (Conversation #{memory_entity.conversation_count})\n"
            )
        else:
            print("✅ Response played.\n")


if __name__ == "__main__":
    interactive_chat()
