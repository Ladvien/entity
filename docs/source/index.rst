.. Entity Framework documentation master file

Entity Framework 🚀
=====================

**Build Production-Ready AI Agents 10x Faster**

.. image:: https://badge.fury.io/py/entity-core.svg
   :target: https://badge.fury.io/py/entity-core
   :alt: PyPI version

.. image:: https://readthedocs.org/projects/entity-core/badge/?version=latest
   :target: https://entity-core.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://img.shields.io/badge/python-3.11+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.11+

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

----

**Stop fighting with boilerplate. Start building intelligent agents.**

Entity transforms AI development from a complex engineering challenge into simple, composable components. While other frameworks force you to write thousands of lines of coupled code, Entity's revolutionary plugin architecture lets you build production-ready agents in hours, not weeks.

.. code-block:: python

   # Traditional approach: 2000+ lines of code, 2-3 weeks
   # Entity approach: This is it. Seriously.

   from entity import Agent
   agent = Agent.from_config("your_agent.yaml")
   await agent.chat("")  # Interactive intelligent agent with memory, tools, safety

Quick Navigation
----------------

.. toctree::
   :maxdepth: 1
   :caption: Getting Started:

   why_entity
   installation
   getting_started
   quickstart

.. toctree::
   :maxdepth: 1
   :caption: Learning:

   examples
   architecture

.. toctree::
   :maxdepth: 1
   :caption: Reference:

   api/modules

.. toctree::
   :maxdepth: 1
   :caption: Community:

   contributing
   changelog

30-Second Demo
--------------

.. code-block:: bash

   # Install Entity
   pip install entity-core

   # Run your first agent
   python -c "
   from entity import Agent
   from entity.defaults import load_defaults
   import asyncio

   async def demo():
       agent = Agent(resources=load_defaults())
       await agent.chat('')  # Interactive chat starts immediately!

   asyncio.run(demo())
   "

Why Choose Entity?
------------------

============================  ==========================  ========================
Feature                       Traditional Frameworks     **Entity Framework**
============================  ==========================  ========================
**Development Time**          2-3 weeks                   **2-3 days**
**Lines of Code**             2000+ lines                 **200 lines**
**Architecture**              Monolithic, coupled         **Plugin-based, modular**
**Configuration**             Code changes required       **YAML-driven**
**Testing**                   Complex integration tests   **Simple unit tests**
**Team Collaboration**        Sequential development      **Parallel plugin dev**
**Maintenance**               Fragile, risky changes     **Isolated, safe updates**
**Production Ready**          DIY monitoring/safety       **Built-in observability**
============================  ==========================  ========================

Ready to Get Started?
----------------------

1. **New to Entity?** → Start with :doc:`why_entity` to understand the value proposition
2. **Ready to code?** → Jump to :doc:`installation` and :doc:`getting_started`
3. **Want hands-on learning?** → Try our :doc:`quickstart` tutorial
4. **Need examples?** → Explore our comprehensive :doc:`examples`
5. **Technical deep-dive?** → Read about Entity's :doc:`architecture`

Links & Resources
-----------------

* `GitHub Repository <https://github.com/Ladvien/entity>`_
* `PyPI Package <https://pypi.org/project/entity-core/>`_
* `Issue Tracker <https://github.com/Ladvien/entity/issues>`_
* `Discussions <https://github.com/Ladvien/entity/discussions>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
