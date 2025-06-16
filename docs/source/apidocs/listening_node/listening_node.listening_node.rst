:py:mod:`listening_neuron.listening_neuron`
=======================================

.. py:module:: listening_neuron.listening_neuron

.. autodoc2-docstring:: listening_neuron.listening_neuron
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`ListeningNeuron <listening_neuron.listening_neuron.ListeningNeuron>`
     - .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron
          :summary:

API
~~~

.. py:class:: ListeningNeuron(config: listening_neuron.config.ListeningNeuronConfig, recording_device: listening_neuron.recording_device.RecordingDevice)
   :canonical: listening_neuron.listening_neuron.ListeningNeuron

   .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron

   .. rubric:: Initialization

   .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron.__init__

   .. py:method:: transcribe(audio_np: numpy.ndarray) -> listening_neuron.transcription.TranscriptionResult
      :canonical: listening_neuron.listening_neuron.ListeningNeuron.transcribe

      .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron.transcribe

   .. py:method:: listen(callback: typing.Optional[typing.Callable[[str, typing.Dict], None]] = None) -> None
      :canonical: listening_neuron.listening_neuron.ListeningNeuron.listen

      .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron.listen

   .. py:method:: _phrase_complete(phrase_time: datetime.datetime, now: datetime.datetime) -> bool
      :canonical: listening_neuron.listening_neuron.ListeningNeuron._phrase_complete

      .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron._phrase_complete

   .. py:method:: _deep_convert_np_float_to_float(data: dict) -> dict
      :canonical: listening_neuron.listening_neuron.ListeningNeuron._deep_convert_np_float_to_float

      .. autodoc2-docstring:: listening_neuron.listening_neuron.ListeningNeuron._deep_convert_np_float_to_float
