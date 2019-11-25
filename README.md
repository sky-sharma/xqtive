# XQtive
Executive for running simple text-based recipe / sequence files PLUS receiving MQTT messages.

PURPOSE:
To enable easy deployment of applications that involve recipes or sequences. Test applications fall into this category.  The rest of this document will address test applications, although other types of applications can be addressed as well.

For example an application that tests a PCB may
(1) Raise a bed of nails; (2) Turn on a power supply that applies a voltage to certain pins; (3) Read a multimeter tied to other pins until the voltage falls within a range or a time-limit is reached.

It is not desirable to write a test application in such a way that when the sequence changes the application has to be modified. For this reason usage of a TEST EXECUTIVE or TEST EXECUTION ENGINE software is desirable.  The Test Executive runs the sequences such that changes to the test only involve changes to the sequences.


INTRO:
XQtive is a Test (or otherwise) Executive framework with the following features:

1. Written in Python3.8.  Should work with Python3.6 onwards but only tested with Python3.8. 
2. Leverages multiprocessing.
3. Interfaces with AWS IoT MQTT.  Interfacing with MosQuiTTo coming soon.
4. Allows a non-programmer to write test sequences using a text-editor and using a simple set of rules / syntax.
5. Allows a programmer with some Python abilities to extend some key classes.
6. Each step in the sequence file corresponds to a state in a state machine. Each of those states subsequently can be defined by sub-states and those by sub-states and so on (currently limited to 999999 levels of nesting / recursion of states). To enable all the states to execute in the proper order PriorityQueues are used.
7. States can be run from a sequence file OR by incoming MQTT messages. States return MQTT messages as feedback. This allows creation of a front-end. A Django-based example front-end is planned for the future.
8. States requested over MQTT can be NORMAL or HIGH priority.  If a HIGH PRIORITY state is received the existing queue is cleared and the HIGH priority state is executed next. 
