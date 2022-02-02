/******************************************************************************
 *
 *  Project:        ECC100 Control Library
 *
 *  Filename:       example.cpp
 *
 *  Purpose:        Minimal example
 *
 *  Author:         N-Hands GmbH & Co KG
 */
/*****************************************************************************/
/* $Id: example.cpp,v 1.5 2016/05/24 15:33:53 trurl Exp $ */

#include <cstdio>
#include <cstdlib>
#include "ecc.h"

#ifdef unix
#include <unistd.h>
#define SLEEP(x) usleep(x*1000)
#else
#include <windows.h>   /* for Sleep */
#define SLEEP(x) Sleep(x)
#endif

static const char * getMessage( int code )
{
  switch( code ) {
  case NCB_Ok:                   return "";
  case NCB_Error:                return "Unspecified error";
  case NCB_Timeout:              return "Communication timeout";
  case NCB_NotConnected:         return "No active connection to device";
  case NCB_DriverError:          return "Error in comunication with driver";
  case NCB_DeviceLocked:         return "Device is already in use by other";
  case NCB_InvalidParam:         return "Parameter out of range";
  case NCB_FeatureNotAvailable:  return "Feature not available";
  default:                       return "Unknown error code";
  }
}


static void exitOnError( const char * context, int code, int devHndl )
{
  if ( code != NCB_Ok ) {
    printf( "Error calling %s: %s\n", context, getMessage( code ) );
    ECC_Close( devHndl );
    exit( 1 );
  }
}


static int selectDevice()
{
  EccInfo * info = NULL;
  unsigned int devCount = ECC_Check( &info );

  for ( unsigned int i = 0; i < devCount; i++ ) {
    printf( "Device found: No=%d ", i );
    if ( info[i] .locked ) {
      printf( "[locked]\n" );
    }
    else {
      printf( "Id=%d\n", info[i] .id );
    }
  }

  int devNo = devCount == 1 ? 0 : -1;
  if ( devCount > 1 ) {
    printf( "Select device: " );
    devNo = getchar() - '0';
    devNo = devNo < 0 || devNo >= (int) devCount ? -1 : devNo;
    printf( "\n" );
  }

  ECC_ReleaseInfo();
  return devNo;
}


int main( int argc, char ** argv )
{
  printf( "ECC100 example program\n" );
  if ( argc > 1 ) {
    // Use the pause to attach a debugger
    printf( "Press Enter to continue\n" );
    getchar();
  }
  Bln32 on = 1, off = 0;  // constants
  int loopCnt = 20;       // wait loop when motor is moving
  Int32 amp   = 30333;    // Amplitude 30.333 V
  Int32 freq  = 2222222;  // Frequency 2.22 kHz
  int devHndl = 0;        // Device handle
  int rc      = NCB_Ok;   // status code

  int devNo = selectDevice();
  if ( devNo < 0 ) {
    printf( "No devices found\n" );
    return 1;
  }

  rc = ECC_Connect( devNo, &devHndl );
  exitOnError( "ECC_Connect", rc, devHndl );
  rc = ECC_controlAmplitude( devHndl, 0, &amp, on );
  exitOnError( "ECC_controlAmplitude", rc, devHndl );
  rc = ECC_controlFrequency( devHndl, 0, &freq, on );
  exitOnError( "ECC_controlFrequency", rc, devHndl );
  rc = ECC_setReset( devHndl, 0 );
  exitOnError( "ECC_setReset", rc, devHndl );
  rc = ECC_controlOutput( devHndl, 0, &on, on );
  exitOnError( "ECC_controlOutput", rc, devHndl );
  rc = ECC_controlContinousFwd( devHndl, 0, &on, on );
  exitOnError( "ECC_controlContinousFwd", rc, devHndl );

  for ( int i = 0; i < loopCnt; ++i ) {
    Int32 pos;
    rc = ECC_getPosition( devHndl, 0, &pos );
    exitOnError( "ECC_getPosition", rc, devHndl );
    printf( "   Fwd Pos: %g mm\n", pos / 1.e6 );
    SLEEP( 100 );
  }

  rc = ECC_controlContinousFwd( devHndl, 0, &off, on );
  exitOnError( "ECC_controlContinousFwd", rc, devHndl );
  rc = ECC_controlContinousBkwd( devHndl, 0, &on, on );
  exitOnError( "ECC_controlContinousBkwd", rc, devHndl );

  for ( int i = 0; i < loopCnt; ++i ) {
    Int32 pos;
    rc = ECC_getPosition( devHndl, 0, &pos );
    exitOnError( "ECC_getPosition", rc, devHndl );
    printf( "   Bwd Pos: %g mm\n", pos / 1.e6 );
    SLEEP( 100 );
  }

  rc = ECC_controlContinousBkwd( devHndl, 0, &off, on );
  exitOnError( "ECC_controlContinousBkwd", rc, devHndl );
  rc = ECC_Close( devHndl );
  exitOnError( "ECC_Close", rc, devHndl );

  printf( "Success!\n" );
  return 0;
}

