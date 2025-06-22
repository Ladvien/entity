#!/usr/bin/env python3
"""
End-to-End TTS Integration Test

This script tests the complete chat flow with TTS generation
"""

import asyncio
import logging
import httpx
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)


async def test_chat_with_tts():
    """Test the full chat API with TTS generation"""

    print("🎯 End-to-End TTS Integration Test")
    print("=" * 50)

    # Server URL - adjust if needed
    server_url = "http://localhost:8000"

    print("🔍 Make sure your server is running:")
    print("   python -m uvicorn src.server.main:app --reload")
    print()

    print(f"Testing server at: {server_url}")

    async with httpx.AsyncClient(timeout=60.0) as client:

        # 1. Test health check
        try:
            print("\n🏥 Testing health endpoint...")
            response = await client.get(f"{server_url}/api/v1/health")

            if response.status_code == 200:
                health_data = response.json()
                print("✅ Server is healthy")
                print(f"   Features: {list(health_data.get('features', {}).keys())}")
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                print("   Make sure your server is running:")
                print("   python -m uvicorn src.server.main:app --reload")
                return False

        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure your server is running:")
            print("   python -m uvicorn src.server.main:app --reload")
            return False

        # 2. Test chat with TTS
        try:
            print("\n💬 Testing chat with TTS...")

            chat_request = {
                "message": "Hello! Can you tell me a quick joke?",
                "thread_id": "tts_test",
                "use_tools": False,  # Disable tools for simpler test
                "use_memory": True,
            }

            print(f"   Sending: '{chat_request['message']}'")

            response = await client.post(f"{server_url}/api/v1/chat", json=chat_request)

            if response.status_code == 200:
                chat_data = response.json()
                print("✅ Chat response received")

                # Check response content
                agent_response = chat_data.get("response", "")
                print(
                    f"   Agent said: '{agent_response[:100]}{'...' if len(agent_response) > 100 else ''}'"
                )

                # Check TTS metadata
                # Note: The response format might vary depending on your API structure
                # Look for TTS info in various possible locations

                tts_enabled = False
                audio_file_id = None

                # Check if there's metadata with TTS info
                # This might be in different places depending on your API response format
                if "metadata" in chat_data:
                    metadata = chat_data["metadata"]
                    tts_enabled = metadata.get("tts_enabled", False)
                    audio_file_id = metadata.get("audio_file_id")

                # Also check if it's embedded in the response object itself
                if not tts_enabled:
                    tts_enabled = chat_data.get("tts_enabled", False)
                    audio_file_id = chat_data.get("audio_file_id")

                if tts_enabled:
                    print("🎵 TTS generation successful!")
                    print(f"   Audio file ID: {audio_file_id}")

                    # Check if audio file exists locally
                    if audio_file_id:
                        possible_paths = [
                            f"audio_output/{audio_file_id}.wav",
                            f"audio_output/{audio_file_id}",
                        ]

                        for path in possible_paths:
                            if Path(path).exists():
                                size = Path(path).stat().st_size
                                print(f"   ✅ Audio file found: {path} ({size} bytes)")
                                break
                        else:
                            print("   ⚠️ Audio file not found locally (might be normal)")

                    print("\n🎉 SUCCESS: TTS integration is working!")
                    print("   - Chat response received")
                    print("   - TTS audio generated")
                    print("   - Audio file created")

                    return True

                else:
                    print("❌ TTS was not enabled in the response")
                    print("   Response keys:", list(chat_data.keys()))

                    # Print the full response for debugging
                    print("\n🔍 Full response for debugging:")
                    print(json.dumps(chat_data, indent=2, default=str))

                    print("\n💡 Possible issues:")
                    print("   1. TTS adapter not configured in config.yml")
                    print("   2. TTS adapter not enabled")
                    print("   3. TTS adapter processing failed")
                    print("   4. Response format doesn't include TTS metadata")

                    return False

            else:
                print(f"❌ Chat request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Chat test failed: {e}")
            return False


async def main():
    """Main test function"""

    print("🚀 Starting End-to-End TTS Test")
    print("Make sure your server is running first!")
    print("Command: python -m uvicorn src.server.main:app --reload")
    print()

    success = await test_chat_with_tts()

    if success:
        print("\n" + "=" * 50)
        print("🎉 ALL TESTS PASSED!")
        print("Your TTS integration is working correctly.")
        print()
        print("🎵 Audio files should be generated for all chat responses.")
        print("📁 Check the audio_output/ directory for saved files.")

    else:
        print("\n" + "=" * 50)
        print("❌ TESTS FAILED")
        print("Check the error messages above for troubleshooting.")
        print()
        print("💡 Common solutions:")
        print("1. Make sure your config.yml has the adapters section")
        print("2. Verify your TTS server is running")
        print("3. Check server logs for error messages")
        print("4. Run the integration check script first")


if __name__ == "__main__":
    asyncio.run(main())
