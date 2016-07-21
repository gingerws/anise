# anise
one software project administration tool for all environments

Dear Friend, this isn't a github project anymore. Please visit the project homepage: https://pseudopolis.eu/wiki/pino/projs/anise/

Anise is a Python-based execution engine for automation tasks.

Automation tasks exist in software development, and probably all kinds of other sectors. They typically 
require the execution of different smaller and larger tools. 
Complex tasks often need a sequence of many steps to execute, with some steps having dependencies
to each other. 
Manually triggering all these steps in the graphical interfaces of all the involved tools is
possible in theory, but will generate errors and frustration after some cycles.

The automation interfaces of those tools are sometimes easier, but sometimes
they are error-prone. Some tasks may also need to ask the user for some information in an interactive way.
Some smaller parts might also be machine-specific (e.g. filesystem paths or the code how to
access a password vault), while the entire task must be runnable on some different machines.
In some situations, this can lead to a rather intransparent forest of different tools, with unique
oddnesses and special conventions. As the number of different project increases, you will see more and more
different tools, often doing a similar job, but for different platforms or frameworks and, of course, 
with different usage conventions. Spontaneously written glue scripts help in the beginning, but
will explode as the complexity exceeds some threshold.

Typical tasks in software development could be:

- Generating documentation
- Testing
- Automatic code generation
- Creating packages
- Creating a homepage, automatically built from the available
  version information, the packages, the documentation and so on
- Deploying this homepage to a web server
- Handling version information
  - e.g. print it in the manual
- and many more

The anise framework allows you to implement all those tasks in a structured but generic way in a combination of XML and
Python code. Once you have created this stuff at a defined place in your project, anise lets you easily execute your
tasks from command line (or from any editor if you embed it somehow). This gives you a common and easy interface
to all your 'tool glue' code.

The anise engine executes arbitrary Python source
code and provides some additional services like logging, parameter passing from command line, basic graphical user
interface support, a plugin interface, a flexible event system, injecting code and data from other place, 
dependencies between code fragments, and more.

On top of this engine, anise comes with a bunch of implementations which fulfill tasks (or parts of them) of
software development. There is a testing module, a documentation- and homepage-generator, some package building
methods and a lot more. The implementations use the event system in many places in order to allow customization in
a somewhat technical but very flexible way. Even so, those implementations are rather specific and it depends on
the particular case, if, and how many of those implementations are useful.