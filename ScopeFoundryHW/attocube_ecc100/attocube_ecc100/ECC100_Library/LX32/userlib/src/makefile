#*******************************************************************************
#*
#*  Project:        ECC Control Library
#*
#*  Filename:       makefile
#*
#*  Purpose:        GCC makefile for trivial example
#*
#*  Author:         NHands GmbH & Co KG
#*
#********************************************************************************
# $Id: makefile.lx,v 1.1 2013/11/27 18:15:30 trurl Exp $

example : example.o
	gcc -o example -L../lib example.o -lecc

example.o : example.cpp
	gcc -c -g -Wall -O0 -I../inc -o example.o example.cpp

