:py:mod:`listening_neuron.transcription`
======================================

.. py:module:: listening_neuron.transcription

.. autodoc2-docstring:: listening_neuron.transcription
   :allowtitles:

Module Contents
---------------

Classes
~~~~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`Word <listening_neuron.transcription.Word>`
     - .. autodoc2-docstring:: listening_neuron.transcription.Word
          :summary:
   * - :py:obj:`Segment <listening_neuron.transcription.Segment>`
     - .. autodoc2-docstring:: listening_neuron.transcription.Segment
          :summary:
   * - :py:obj:`TranscriptionResult <listening_neuron.transcription.TranscriptionResult>`
     - .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult
          :summary:
   * - :py:obj:`TranscribeConfig <listening_neuron.transcription.TranscribeConfig>`
     - .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig
          :summary:

Data
~~~~

.. list-table::
   :class: autosummary longtable
   :align: left

   * - :py:obj:`PHRASES_TO_IGNORE <listening_neuron.transcription.PHRASES_TO_IGNORE>`
     - .. autodoc2-docstring:: listening_neuron.transcription.PHRASES_TO_IGNORE
          :summary:

API
~~~

.. py:data:: PHRASES_TO_IGNORE
   :canonical: listening_neuron.transcription.PHRASES_TO_IGNORE
   :value: ['', 'urn.com urn.schemas-microsoft-com.h']

   .. autodoc2-docstring:: listening_neuron.transcription.PHRASES_TO_IGNORE

.. py:class:: Word
   :canonical: listening_neuron.transcription.Word

   .. autodoc2-docstring:: listening_neuron.transcription.Word

   .. py:attribute:: word
      :canonical: listening_neuron.transcription.Word.word
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Word.word

   .. py:attribute:: start
      :canonical: listening_neuron.transcription.Word.start
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Word.start

   .. py:attribute:: end
      :canonical: listening_neuron.transcription.Word.end
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Word.end

   .. py:attribute:: probability
      :canonical: listening_neuron.transcription.Word.probability
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Word.probability

   .. py:method:: load(data)
      :canonical: listening_neuron.transcription.Word.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.transcription.Word.load

   .. py:method:: to_dict()
      :canonical: listening_neuron.transcription.Word.to_dict

      .. autodoc2-docstring:: listening_neuron.transcription.Word.to_dict

.. py:class:: Segment
   :canonical: listening_neuron.transcription.Segment

   .. autodoc2-docstring:: listening_neuron.transcription.Segment

   .. py:attribute:: id
      :canonical: listening_neuron.transcription.Segment.id
      :type: int
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.id

   .. py:attribute:: seek
      :canonical: listening_neuron.transcription.Segment.seek
      :type: int
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.seek

   .. py:attribute:: start
      :canonical: listening_neuron.transcription.Segment.start
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.start

   .. py:attribute:: end
      :canonical: listening_neuron.transcription.Segment.end
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.end

   .. py:attribute:: text
      :canonical: listening_neuron.transcription.Segment.text
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.text

   .. py:attribute:: tokens
      :canonical: listening_neuron.transcription.Segment.tokens
      :type: typing.List[int]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.tokens

   .. py:attribute:: temperature
      :canonical: listening_neuron.transcription.Segment.temperature
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.temperature

   .. py:attribute:: avg_logprob
      :canonical: listening_neuron.transcription.Segment.avg_logprob
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.avg_logprob

   .. py:attribute:: compression_ratio
      :canonical: listening_neuron.transcription.Segment.compression_ratio
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.compression_ratio

   .. py:attribute:: no_speech_prob
      :canonical: listening_neuron.transcription.Segment.no_speech_prob
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.no_speech_prob

   .. py:attribute:: words
      :canonical: listening_neuron.transcription.Segment.words
      :type: typing.List[listening_neuron.transcription.Word]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.words

   .. py:method:: __post_init__()
      :canonical: listening_neuron.transcription.Segment.__post_init__

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.__post_init__

   .. py:method:: load(data)
      :canonical: listening_neuron.transcription.Segment.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.load

   .. py:method:: to_dict()
      :canonical: listening_neuron.transcription.Segment.to_dict

      .. autodoc2-docstring:: listening_neuron.transcription.Segment.to_dict

.. py:class:: TranscriptionResult
   :canonical: listening_neuron.transcription.TranscriptionResult

   .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult

   .. py:attribute:: text
      :canonical: listening_neuron.transcription.TranscriptionResult.text
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.text

   .. py:attribute:: segments
      :canonical: listening_neuron.transcription.TranscriptionResult.segments
      :type: list[listening_neuron.transcription.Segment]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.segments

   .. py:attribute:: language
      :canonical: listening_neuron.transcription.TranscriptionResult.language
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.language

   .. py:attribute:: processing_secs
      :canonical: listening_neuron.transcription.TranscriptionResult.processing_secs
      :type: int
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.processing_secs

   .. py:attribute:: local_starttime
      :canonical: listening_neuron.transcription.TranscriptionResult.local_starttime
      :type: datetime.datetime
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.local_starttime

   .. py:attribute:: processing_rolling_avg_secs
      :canonical: listening_neuron.transcription.TranscriptionResult.processing_rolling_avg_secs
      :type: float
      :value: 0

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.processing_rolling_avg_secs

   .. py:method:: __post_init__()
      :canonical: listening_neuron.transcription.TranscriptionResult.__post_init__

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.__post_init__

   .. py:method:: load(data)
      :canonical: listening_neuron.transcription.TranscriptionResult.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.load

   .. py:method:: to_dict()
      :canonical: listening_neuron.transcription.TranscriptionResult.to_dict

      .. autodoc2-docstring:: listening_neuron.transcription.TranscriptionResult.to_dict

.. py:class:: TranscribeConfig
   :canonical: listening_neuron.transcription.TranscribeConfig

   .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig

   .. py:attribute:: model
      :canonical: listening_neuron.transcription.TranscribeConfig.model
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.model

   .. py:attribute:: device
      :canonical: listening_neuron.transcription.TranscribeConfig.device
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.device

   .. py:attribute:: verbose
      :canonical: listening_neuron.transcription.TranscribeConfig.verbose
      :type: bool | None
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.verbose

   .. py:attribute:: temperature
      :canonical: listening_neuron.transcription.TranscribeConfig.temperature
      :type: typing.Union[float, typing.Tuple[float, ...]]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.temperature

   .. py:attribute:: compression_ratio_threshold
      :canonical: listening_neuron.transcription.TranscribeConfig.compression_ratio_threshold
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.compression_ratio_threshold

   .. py:attribute:: logprob_threshold
      :canonical: listening_neuron.transcription.TranscribeConfig.logprob_threshold
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.logprob_threshold

   .. py:attribute:: no_speech_threshold
      :canonical: listening_neuron.transcription.TranscribeConfig.no_speech_threshold
      :type: float
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.no_speech_threshold

   .. py:attribute:: condition_on_previous_text
      :canonical: listening_neuron.transcription.TranscribeConfig.condition_on_previous_text
      :type: bool
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.condition_on_previous_text

   .. py:attribute:: word_timestamps
      :canonical: listening_neuron.transcription.TranscribeConfig.word_timestamps
      :type: bool
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.word_timestamps

   .. py:attribute:: prepend_punctuations
      :canonical: listening_neuron.transcription.TranscribeConfig.prepend_punctuations
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.prepend_punctuations

   .. py:attribute:: append_punctuations
      :canonical: listening_neuron.transcription.TranscribeConfig.append_punctuations
      :type: str
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.append_punctuations

   .. py:attribute:: initial_prompt
      :canonical: listening_neuron.transcription.TranscribeConfig.initial_prompt
      :type: typing.Optional[str]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.initial_prompt

   .. py:attribute:: clip_timestamps
      :canonical: listening_neuron.transcription.TranscribeConfig.clip_timestamps
      :type: typing.Union[str, typing.List[float]]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.clip_timestamps

   .. py:attribute:: hallucination_silence_threshold
      :canonical: listening_neuron.transcription.TranscribeConfig.hallucination_silence_threshold
      :type: typing.Optional[float]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.hallucination_silence_threshold

   .. py:attribute:: phrases_to_ignore
      :canonical: listening_neuron.transcription.TranscribeConfig.phrases_to_ignore
      :type: list[str]
      :value: None

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.phrases_to_ignore

   .. py:method:: load(data)
      :canonical: listening_neuron.transcription.TranscribeConfig.load
      :classmethod:

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.load

   .. py:method:: __post_init__()
      :canonical: listening_neuron.transcription.TranscribeConfig.__post_init__

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.__post_init__

   .. py:method:: to_dict()
      :canonical: listening_neuron.transcription.TranscribeConfig.to_dict

      .. autodoc2-docstring:: listening_neuron.transcription.TranscribeConfig.to_dict
