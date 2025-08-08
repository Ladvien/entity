.. Entity documentation master file

Welcome to Entity Documentation
================================

Entity is a flexible, plugin-based framework for building AI agents with a unified architecture 
combining a 4-layer resource system with a 6-stage workflow.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   getting_started
   installation
   architecture
   api/modules
   examples
   contributing
   changelog

Key Features
------------

* **Zero-config defaults** - Works immediately with sensible defaults
* **4-Layer Resource System** - Clean separation of infrastructure, resources, and agents
* **6-Stage Workflow** - INPUT → PARSE → THINK → DO → REVIEW → OUTPUT
* **Plugin Architecture** - Extensible through plugins for each workflow stage
* **Production Ready** - Built-in logging, testing, and deployment support

Quick Start
-----------

.. code-block:: python

   from entity import Agent

   # Create agent with zero configuration
   agent = Agent()
   
   # Chat with the agent
   response = await agent.chat("What's 5 * 7?")
   print(response)

Installation
------------

.. code-block:: bash

   pip install entity

Or with Poetry:

.. code-block:: bash

   poetry add entity

Requirements
------------

* Python 3.11 or higher
* Optional: Docker for infrastructure components
* Optional: CUDA-capable GPU for local LLM inference

License
-------

This project is licensed under the MIT License.

Links
-----

* `GitHub Repository <https://github.com/Ladvien/entity>`_
* `PyPI Package <https://pypi.org/project/entity/>`_
* `Issue Tracker <https://github.com/Ladvien/entity/issues>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`