:py:mod:`listening_neuron.config`
=================================

.. py:module:: listening_neuron.config

.. autodoc2-docstring:: listening_neuron.config
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`ListeningNeuronConfig <listening_neuron.config.ListeningNeuronConfig>`
     - .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig
          :summary:
   * - :py:obj:`Config <listening_neuron.config.Config>`
     - .. autodoc2-docstring:: listening_neuron.config.Config
          :summary:

API
~~~

.. py:class:: ListeningNeuronConfig
   :canonical: listening_neuron.config.ListeningNeuronConfig

   .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig

   .. py:attribute:: record_timeout
      :canonical: listening_neuron.config.ListeningNeuronConfig.record_timeout
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.record_timeout

   .. py:attribute:: phrase_timeout
      :canonical: listening_neuron.config.ListeningNeuronConfig.phrase_timeout
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.phrase_timeout

   .. py:attribute:: in_memory
      :canonical: listening_neuron.config.ListeningNeuronConfig.in_memory
      :type: bool
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.in_memory

   .. py:attribute:: log
      :canonical: listening_neuron.config.ListeningNeuronConfig.log
      :type: bool
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.log

   .. py:attribute:: transcribe_config
      :canonical: listening_neuron.config.ListeningNeuronConfig.transcribe_config
      :type: listening_neuron.transcription.TranscribeConfig
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.transcribe_config

   .. py:method:: load(data)
      :canonical: listening_neuron.config.ListeningNeuronConfig.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.load

   .. py:method:: __post_init__()
      :canonical: listening_neuron.config.ListeningNeuronConfig.__post_init__

      .. autodoc2-docstring:: listening_neuron.config.ListeningNeuronConfig.__post_init__

.. py:class:: Config
   :canonical: listening_neuron.config.Config

   .. autodoc2-docstring:: listening_neuron.config.Config

   .. py:attribute:: listening_neuron
      :canonical: listening_neuron.config.Config.listening_neuron
      :type: listening_neuron.config.ListeningNeuronConfig
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.Config.listening_neuron

   .. py:attribute:: mic_config
      :canonical: listening_neuron.config.Config.mic_config
      :type: listening_neuron.mic.MicConfig
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.Config.mic_config

   .. py:attribute:: logging_config
      :canonical: listening_neuron.config.Config.logging_config
      :type: listening_neuron.logging_config.LoggingConfig | None
      :value: None

      .. autodoc2-docstring:: listening_neuron.config.Config.logging_config

   .. py:method:: load(path)
      :canonical: listening_neuron.config.Config.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.config.Config.load

   .. py:method:: __post_init__()
      :canonical: listening_neuron.config.Config.__post_init__

      .. autodoc2-docstring:: listening_neuron.config.Config.__post_init__
