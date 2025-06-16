from rich import print
import logging

from listening_neuron import Config, RecordingDevice, ListeningNeuron
from listening_neuron.transcription import TranscriptionResult


def transcription_callback(text: str, result: TranscriptionResult) -> None:
    print(result)


def main():
    config = Config.load("config.yaml")
    logging.info("Using config: ")
    logging.info(config)

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    print(config)
    recording_device = RecordingDevice(config.mic_config)
    listening_neuron = ListeningNeuron(
        config.listening_neuron,
        recording_device,
    )

    # Cue the user that we're ready to go.
    print("Model loaded.\n")
    listening_neuron.listen(transcription_callback)


if __name__ == "__main__":
    main()
