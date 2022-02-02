#ifndef __REMOTE_TEST_LIB_H_
#define __REMOTE_TEST_LIB_H_

#include <QLibrary>
#include "remote_spm.h"

class CRemoteCtrl: public QObject
{
public:
	CRemoteCtrl( const QString & folderName, QObject * parent = 0 );
	bool isLoaded();
	const QString & resolveError();
	
	typedef bool (CALL_T *TInitialization)();
	TInitialization initialization;

	typedef void (CALL_T *TFinalization)();
    TFinalization finalization;

	typedef bool (CALL_T *TIsConnected)();
    TIsConnected isConnected;

	//typedef const char * (CALL_T *TErrorString)();
	//TErrorString errorString;

	typedef void (CALL_T *TSendLogMessage)( char * input, char * response );
    TSendLogMessage sendLogMessage;

	typedef void (CALL_T *TInitTestCallback)();
	TInitTestCallback initTestCallback;

	typedef void (CALL_T *TInitTestScanCallback)();
	TInitTestScanCallback initTestScanCallback;

	typedef void (CALL_T *TSetCallback)( TCallback proc );
    TSetCallback setCallback;

	typedef void (CALL_T *TSetScanCallback)( TScanCallback proc );
    TSetScanCallback setScanCallback;

	typedef void (CALL_T *TSetRestartLineCallback)( TRestartLineCallback proc );
    TSetRestartLineCallback setRestartLineCallback;

	typedef int (CALL_T *TServerInterfaceVersion)();
	TServerInterfaceVersion serverInterfaceVersion;

	typedef int (CALL_T *TClientInterfaceVersion)();
	TClientInterfaceVersion clientInterfaceVersion;

	typedef bool (CALL_T *TIsServerCompatible)();
	TIsServerCompatible isServerCompatible;

	typedef float (CALL_T *TAxisRange)( char * axisId );
	TAxisRange axisRange;

	typedef float (CALL_T *TAxisPosition)( char * axisId );
	TAxisPosition axisPosition;

	typedef bool (CALL_T *TSetAxisPosition)( char * axisId, float * value, float sweepTime );
	TSetAxisPosition setAxisPosition;

	typedef bool (CALL_T *TSetAxesPositions)( int axesCnt, char axesIds[][MAX_AXIS_ID_LEN], float * values, float sweepTime );
	TSetAxesPositions setAxesPositions;

	typedef float (CALL_T *TAxisSetpoint)( char * axisId );
	TAxisSetpoint axisSetpoint;

	typedef int (CALL_T *TSignalsList)( char names[][MAX_SIG_NAME_LEN], char units[][MAX_SIG_NAME_LEN] );
	TSignalsList signalsList;

	typedef bool (CALL_T *TSetupScanCommon)( char * planeId, int linePts, TScanMode mode, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	TSetupScanCommon setupScanCommon;

	typedef bool (CALL_T *TSetupScanLine)( float x0, float y0, float x1, float y1, float tforw, float tback );
	TSetupScanLine setupScanLine;

	typedef bool (CALL_T *TExecScanPoint)( int * size, float * vals );
	TExecScanPoint execScanPoint;

	typedef void (CALL_T *TFinitScan)();
	TFinitScan finitScan;

	typedef bool (CALL_T *TExecScanLine)( float tpoint );
	TExecScanLine execScanLine;

	typedef bool (CALL_T *TSetTriggering)( bool enable );
	TSetTriggering setTriggering;

	typedef bool (CALL_T *TProbeSweepZ)( float from, float to, int pts, float sweepT, float kIdleMove, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	TProbeSweepZ probeSweepZ;
	typedef bool (CALL_T *TBreakProbeSweepZ)();
	TBreakProbeSweepZ breakProbeSweepZ;
	typedef bool (CALL_T *TProbeLift)( float lift, float triggerTime );
	TProbeLift probeLift;
	typedef bool (CALL_T *TProbeLand)();
	TProbeLand probeLand;

	typedef bool (CALL_T *TProbeLand2)();
	TProbeLand2 probeLand2;

	typedef bool (CALL_T *TSetupPlaneScan)( int linePts, TScanMode mode, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	TSetupPlaneScan setupPlaneScan;
	typedef bool (CALL_T *TSetPlanePoints)( int ptsCnt, float * x, float * y, float * z );
	TSetPlanePoints setPlanePoints;
	typedef void (CALL_T *TSetPlaneLift)( float lift, float liftback );
	TSetPlaneLift setPlaneLift;

	typedef bool (CALL_T *TSetupScan2Pass)( int linePts, TScanMode mode, int sigsCnt, int pass1SigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	TSetupScan2Pass setupScan2Pass;
	typedef bool (CALL_T *TSetup2PassLine)( float x0, float y0, float x1, float y1, float tpass1, float tpass2, float tpass2back );
	TSetup2PassLine setup2PassLine;
	typedef void (CALL_T *TSet2PassLift)( float lift, float liftback );
	TSet2PassLift set2PassLift;
	typedef void (CALL_T *TSet2PassTriggering)( bool pass1On, bool pass2On );
	TSet2PassTriggering set2PassTriggering;

private:
	QLibrary * m_lib;
	QString m_resolveError;
};


#endif


