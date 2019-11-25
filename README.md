# XQtive
An executive for running sequences of steps defined in a simple text file.  Also executes steps requested over MQTT.

PURPOSE:
To enable easy deployment of applications that involve recipes or sequences. Test applications fall into this category.  The rest of this document will address test applications, although other types of applications can be addressed as well.

For example an application that tests a PCB may
(1) Raise a bed of nails; (2) Turn on a power supply that applies a voltage to certain pins; (3) Read a multimeter tied to other pins until the voltage falls within a range or a time-limit is reached.

It is not desirable to write a test application in such a way that when the sequence changes the application has to be modified. For this reason usage of a TEST EXECUTIVE or TEST EXECUTION ENGINE software is desirable.  The Test Executive runs the sequences such that changes to the test only involve changes to the sequences. XQtive is such a Test (or otherwise) Executive framework.

# The terms "step" and "state" are used interchangeably in the rest of this document.

FEATURES:
1. Written in Python3.8.  Should work with Python3.6 onwards but only tested with Python3.8. 
2. Leverages multiprocessing.
3. Interfaces with AWS IoT MQTT.  Interfacing with MosQuiTTo coming soon.
4. Allows a non-programmer to write test sequences using a text-editor and using a simple set of rules / syntax.
5. Allows a programmer with some Python abilities to extend some key classes.
6. Each step in the sequence file corresponds to a state in a state machine. Each of those states subsequently can be defined by sub-states and those by sub-states and so on. To enable all the states to execute in the proper order PriorityQueues are used.
7. States can be run from a sequence file OR by incoming MQTT messages. States return MQTT messages as feedback. This allows creation of a front-end.
8. States requested over MQTT can be NORMAL or HIGH priority.  If a HIGH PRIORITY state is received the existing queue is cleared and the HIGH priority state is executed next. 

EXAMPLE SEQUENCE FILE:

------------
//Set output
PWR_SPLY_OUTPUT;31

//Poll actual voltage
POLL;20;FLOAT;VOLTS;ABOVE;34

// Power off
PWR_SPLY_OFF

-------------

RULES FOR WRITING SEQUENCE FILES:
1. Steps may refer to states existing in the original framework OR states included through extension.
2. Blank lines and steps preceded by '//' are ignored.
3. All steps are considered NORMAL priority.
4. A step may be made of sub-steps. Those sub-steps may be "public" (can be directly requested from a sequence file or over MQTT) or "private" (cannot be requested from a sequence file or over MQTT). In the example file "PWR_SPLY_OUTPUT" may be made up of "TurnOnPowerSupply", "SetVoltage", "WaitForStabilization" and "CloseRelay". Those states cannot be called directly.
5. If a step is made of sub-steps, those sub-steps will be enqueued at a HIGHER than NORMAL priority so that they execute BEFORE the next step in the sequence file.  Referring to (4) above, once "PWR_SPLY_OUTPUT" is requested, "TurnOnPowerSupply" thru "CloseRelay" have to happen BEFORE "POLL..." is requested.
7. POLL allows reading of a variable UNTIL it meets a criterion OR a time-limit is reached. It is NON-blocking, i.e. allows interruption from a HIGH priority step sent over MQTT.
8. POLL syntax is f"POLL;{time-limit-in-sec};{variable-type};{variable-name};{comparison-type};{threshold1};{optional-threshold-2}". comparison types are "MATCH", "ABOVE", "BELOW", "BETWEEN".

CAVEATS:
1. Steps can be made of sub-steps, which may themselves be made of sub-steps and so on up to 999999 levels of nesting / recursion. A limit IS needed but can be configured to be higher if ever needed.
2. Steps requested over MQTT can be NORMAL or HIGH priority (configurable). An incoming HIGH priority request clears the existing queue and can request up to ONE followup step.

RULES FOR CLASS EXTENSION:
The core of XQTive is the XQtiveStateMachine class. Included among the methods of this class are States. If extending this class some rules have to be followed. Rules coming soon.

FEATURES IN THE WORKS:
1. A Django-based example front-end.
2. Allowing extensions for Test results; i.e Pass / Fail per step and for entire sequence.
