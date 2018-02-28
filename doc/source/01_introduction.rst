Introduction
============

fishy is a toolkit for filesystem based data hiding techniques implemented in
Python. It collects various common exploitation methods that make use of
existing data structures on the filesystem layer, for hiding data from
conventional file access methods. This toolkit is intended to introduce people
to the concept of established anti-forensic methods associated with data
hiding.

In our research regarding existing tools for filesystem based data hinding
techniques we only came up with a hand full of tool. None of these provide a
consistent interface for multiple filesystems and various hiding techniques.
For most of them it seemed, that development has been stopped.

With this background, there is no currently active framework for filesystem
based data hinding techniques, other than fishy. As fishy aimes to provide an
easy to use framework for creating new hiding techniques, this project might be
useful for all security researchers, which are concerned with data hiding.

This toolkit provides a cli interface for hiding data via the command line. Also
the implemented hiding techniques can be used in other projects by importing
fishy as a library. Besides that, fishy can also act as a framework to easily
implement custom hiding techniques.

Limitations
-----------

`fishy` is currently only tested to run under linux. Other operating systems may
provide different functions to access low level devices.

Although it is possible to hide multiple different files on the filesystem,
`fishy` is currently not capable of managing them. So, it is up to the user to avoid
overwritten data.

`fishy` does not encrypt the data it hides. If the user needs encryption, it is
up to him to apply the encryption before he hides the data with this tool. The same
applies to data integrity functionality.

See also
--------

During our research we mainly found two tools that implement filesystem based
data hiding techniques and that seemed to be in a broader use. First there is
`bmap <http://www.gupiaoya.com/Soft/Soft_6823.htm>`_, a linux tool for hiding
data in ntfs slack space. This project seems to have no active website and
downloads of this tool can only found on some shady tool collection sites.

The second tool we found was `slacker.exe
<http://www.bishopfox.com/resources/tools/other-free-tools/mafia/>`_, a windows
tool for hiding data in ntfs slack space. This tool was developed by Bishop Fox
and seems to be included into the metasploit framework, at some time. The actual
download on their website is disabled.

Documentation Overview
----------------------

This paragraph will provide a brief overview of this documentation, giving a short summary of its structure.
You will be introduced to the paper by its abstract and introductory sections.
The `getting started` section gives beginners a fast start with the tool.
After this basic introduction on how this toolkit can be used, we give some background
information about `filesystem datastructures` and a brief explanation of each implemented `hiding technique`.
The following `architecture overview` gives an introduction to fishy's core design principles and structures.
The `module reference` documents the most important modules and classes, which you
might use, if you want to integrate fishy into your own projects.
In the `evaluation` section, all implemented hiding techniques are shortly rated for
their gained capacity, stability and their propability of detection.
The `future work` section ends this documentation.
