# anise
one software project administration tool for all environments

Read README.pdf!

Anise helps you to implement a common mechanism for executing all automated tasks for all your software projects.
The usage scenario is a developer (or a team) working on many different projects with different frameworks
and different tools. Anise can streamline such a chaos of tools. Typical tasks you would add to an anise-aware
project can be:

- generating documentation
- creating packages
- handling version information
  - e.g. print it in the manual
- creating a homepage automatically built from the available
  version information, the packages, the documentation and so on
- deploying this homepage to a web server
- unit testing
- ... or whatever your project needs

Anise provides a Python based infrastructure, while you will need to implement some parts in order to adapt the
behavior to your project's needs. Anise contains some ready-to-use implementations for some tasks (like
building binaries via qmake, debian and some other packages, svn interaction, doxygen, ...), so you can directly
use it without non-trivial additional coding to do all kinds of stuff, including generating documentations,
packages and a homepage. However, chances are good that you will have to help out with some own implementations.

Your part as a project developer is to create a *project description* file, which contains all project metadata and
custom implementations of some tasks, and add this file to your project.
