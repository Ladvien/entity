#!/usr/bin/env python3
"""
TTS Adapter Test Script

This script helps you test and debug the TTS adapter integration
independently of the main application.
"""

import asyncio
import logging
from pathlib import Path
from datetime import datetime

from src.core.config import EntityServerConfig
from src.adapters.tts_adapter import TTSOutputAdapter
from src.shared.models import ChatInteraction

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def test_tts_adapter():
    """Test the TTS adapter functionality"""

    print("🎙️ TTS Adapter Test Script")
    print("=" * 50)

    # Load configuration
    try:
        config = EntityServerConfig.config_from_file("config/config.yml")
        print(f"✅ Configuration loaded successfully")
        print(f"   TTS Server: {config.tts.base_url}")
        print(f"   Voice: {config.tts.voice_name}")
        print(f"   Speed: {config.tts.speed}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return

    # Create TTS adapter
    try:
        tts_adapter = TTSOutputAdapter(tts_config=config.tts, enabled=True)
        print(f"✅ TTS Adapter created successfully")
    except Exception as e:
        print(f"❌ Failed to create TTS adapter: {e}")
        return

    # Test server connection
    print("\n🔍 Testing TTS server connection...")
    try:
        is_healthy = await tts_adapter.test_connection()
        if is_healthy:
            print("✅ TTS server connection successful")
        else:
            print("❌ TTS server connection failed")
            print("   Make sure your speech server is running and accessible")
            return
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return

    # Test voice listing
    print("\n🎤 Testing voice listing...")
    try:
        voices = await tts_adapter.list_available_voices()
        if voices:
            print(f"✅ Found {len(voices)} available voices:")
            for voice in voices[:3]:  # Show first 3
                voice_name = voice.get("voice_name", voice.get("name", "Unknown"))
                print(f"   - {voice_name}")
        else:
            print("⚠️ No voices returned (this might be normal)")
    except Exception as e:
        print(f"⚠️ Could not list voices: {e}")

    # Test text synthesis
    print("\n🗣️ Testing text synthesis...")
    test_text = "Hello, this is a test of the TTS adapter integration."

    try:
        # Create a mock chat interaction
        interaction = ChatInteraction(
            thread_id="test_thread",
            timestamp=datetime.utcnow(),
            raw_input="Test input",
            raw_output="Test output",
            response=test_text,
            tools_used=[],
            memory_context_used=False,
            memory_context="",
            use_tools=True,
            use_memory=True,
        )

        print(f"   Text to synthesize: '{test_text}'")

        # Process through adapter
        processed_interaction = await tts_adapter.process_response(interaction)

        # Check results
        if processed_interaction.metadata.get("tts_enabled"):
            print("✅ TTS synthesis successful!")
            audio_file_id = processed_interaction.metadata.get("audio_file_id")
            print(f"   Audio file ID: {audio_file_id}")

            duration = processed_interaction.metadata.get("audio_duration")
            if duration:
                print(f"   Duration: {duration}s")

            # Check if local file was created
            local_path = processed_interaction.metadata.get("local_path")
            if local_path and Path(local_path).exists():
                print(f"   Local file: {local_path}")
                print(f"   File size: {Path(local_path).stat().st_size} bytes")

        else:
            print("❌ TTS synthesis failed")
            error = processed_interaction.metadata.get("tts_error")
            if error:
                print(f"   Error: {error}")

    except Exception as e:
        print(f"❌ Synthesis test failed: {e}")
        logger.exception("Detailed error information:")

    # Test cleanup
    print("\n🧹 Cleaning up...")
    try:
        await tts_adapter.close()
        print("✅ TTS adapter closed successfully")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")

    print("\n" + "=" * 50)
    print("🎯 TTS Adapter test completed!")


async def test_direct_speech_synthesis():
    """Test direct speech synthesis without the adapter wrapper"""

    print("\n🎙️ Direct Speech Synthesis Test")
    print("=" * 50)

    config = EntityServerConfig.config_from_file("config/config.yml")

    # Create adapter and test direct synthesis
    tts_adapter = TTSOutputAdapter(config.tts, enabled=True)

    test_texts = [
        "Short test.",
        "This is a longer test with multiple sentences. It should work fine.",
        "Testing special characters: Hello! How are you? Great, thanks.",
    ]

    for i, text in enumerate(test_texts):
        print(f"\n📝 Test {i+1}: '{text[:50]}{'...' if len(text) > 50 else ''}'")

        try:
            result = await tts_adapter._synthesize_speech(text, f"test_{i}")

            if result:
                print(f"✅ Success: {result}")
            else:
                print("❌ Failed to synthesize")

        except Exception as e:
            print(f"❌ Error: {e}")

    await tts_adapter.close()


async def main():
    """Main test function"""
    print("🚀 Starting TTS Adapter Tests")
    print("=" * 60)

    # Test 1: Full adapter integration
    await test_tts_adapter()

    # Test 2: Direct synthesis
    try:
        await test_direct_speech_synthesis()
    except Exception as e:
        print(f"❌ Direct synthesis test failed: {e}")

    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
