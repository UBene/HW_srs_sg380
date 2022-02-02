#*******************************************************************************
#  Project:        ECC100 Control Library
#
#  Filename:       makefile
#
#  Purpose:        MSVC makefile for trivial example
#
#  Author:         N-Hands GmbH & Co KG
#*******************************************************************************
# $Id: makefile.win,v 1.2 2013/12/16 15:10:18 trurl Exp $

example.exe : example.obj ..\lib\ecc.lib
	link /NOLOGO /DEBUG /SUBSYSTEM:CONSOLE example.obj ..\lib\ecc.lib

example.obj :  example.cpp
	cl -nologo -c -Zi -W3 -MDd -I..\inc example.cpp

