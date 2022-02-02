#ifdef REMOTESPM_DLL
    #ifdef REMOTESPM_MAKE_DLL
        #define EXPORT __declspec(dllexport)
    #else
        #define EXPORT __declspec(dllimport)
    #endif
#else
    #define EXPORT
#endif

//#define CALL_T __stdcall
#define CALL_T __cdecl

// REMOTE_SPM.DLL
// The library for remote access from another application to aist-application.
// It needs following third-party libs:
// iceutil33.dll
// ice33.dll
// bzip2.dll

// REMOTE_TEST.EXE
// The example-application for testing the remote_spm.dll is ../remote_test.exe,
// so it is the folder one level up - the same folder where there is aist.exe.
// The exe file must be in the folder because it uses QtGui4.dll and QtCore4.dll;
// it looks for the remote_spm.dll and auxilurialy third-party libs inside "remote_spm" subfolder.
// The source code are in files:
// remote_test.cpp,h and remote_test_lib.cpp,h.
// The methods loaded into application via CRemoteCtrl class object which is defined in remote_test_lib.h.
// All methods are always called in main application thread only, except the methods of types TScanCallback and TCallback,
// which are run by the library in some axiluary thread. Pay attention how these two methods, especially TScanCallback,
// are binded with the main thread methods (see comments in the remote_test.cpp).

// ******** Initializing the remote control in SPM-software.
// MANUAL initializing of the SPM server in aist software:
// Run the script macros/qnami/remote_ctrl.lua; check the "Enable" button on the open form.
// Then you can close the form. The server may be initialized both after “Initialize SPM” or “View only mode”.
// You can run the server many times, then need to reestablish the connection from your app.
// AUTOMATIC initializing of the SPM server:
// In the Macro executor window open user_init.lua to edit. For this select the file from the list,
// press the open-folder-icon-button (the second button on the left panel of the “Macro executor”).
// In the opened file uncomment the code-strings under “*** SPM remote control (Qnami)”.
// Next time you run the software, no matter if press the “Initialize SPM” or “View only mode”, the server will be run.


// The type declaration for user-function (client-side), which supposed to be called
// from host-side (SPM-software) at arbitrary moment.
// proc_index = 1 means that probe XYZ-position (or sample XYZ-position) was changed from SPM-software.
// Partially SPM software calls TCallback function when scan process is finished (not the scanning presented in this library)
// or if operator moves probe maually for some operations.
// proc_index = 2 means that XYZ-coordinates of second (objective) scanner were changed.
typedef void ( *TCallback )( int proc_index );

// Familiar to TCallback. The arguments are a floating-number array and its size.
// During scan process (ExecScanLine) SPM-software sends in series the signals' arrays
// (topography-signal, etc.), measured in each scan point.
// size == 0 means the end of the line.
typedef void ( *TScanCallback )( int size, float * vals );

// Called back after ExecScanLine, when PC-controller connection error occurs
// call implies that the scan-line execution was restarted
// call may occur at any moment after ExecScanLine, say, even during movement to first scan point,
// i.e. when there were no any trigger pulses performed and no AFM signals points were measured/sent
typedef void ( *TRestartLineCallback )();

#define MAX_SIG_NAME_LEN	40
#define MAX_AXIS_ID_LEN		8

#define INTERFACE_VERSION	11

enum TScanMode
{
	LINE_SCAN,
	POINT_SCAN
};

extern "C"
{
	EXPORT bool CALL_T Initialization();	// Connect to SPM-software
	EXPORT void CALL_T Finalization();		// Disconnect
	EXPORT bool CALL_T IsConnected();

	// Register call-back user-functions
	EXPORT void CALL_T SetCallback( TCallback proc );
	EXPORT void CALL_T SetScanCallback( TScanCallback proc );
	EXPORT void CALL_T SetRestartLineCallback( TRestartLineCallback proc );

	// ******** SendLogMessage, InitTestCallback, and InitTestScanCallback methods are to premiliary
	// familiarize with the library utilizing. No real SPM-system is of need.

	// Send the message to display in the Log-window in the SPM-software.
	// After get the message, the SPM-software responses;
	// the response-message data is returned to the "response" char-array
	// (a '\0'-terminated string).
	EXPORT void CALL_T SendLogMessage( char * input, char * response );

	// Run the procedure inside the SPM-software, which initializes 5 calls of the client-function,
	// registered by "SetCallback". The interval between calls is of 2 seconds.
	// Each time the transferred index ("proc_index" variable of the TCallback function) is increased.
	EXPORT void CALL_T InitTestCallback();

	// Run the procedure inside the SPM-software, which initializes 7 calls of the client-function,
	// registered by SetScanCallback. The interval between calls is 1 second.
	// "vals" arrays are of different size for each call.
	EXPORT void CALL_T InitTestScanCallback();

	// server returns the version of remote spm modules inside aist-software
	// client returns the version of remote_spm.dll
	EXPORT int CALL_T ServerInterfaceVersion();
	EXPORT int CALL_T ClientInterfaceVersion();

	// The client/server versions may be different, but still comapatible.
	// If ClientInterfaceVersion() > ServerInterfaceVersion() the answer is produced by client part,
	// otherwise the answer comes from the server.
	EXPORT bool CALL_T IsServerCompatible();


	// ******** SPM control methods.

	// axisId: X, Y, Z (or X1, Y1, Z1); X2, Y2, Z2; or lowercase; units: um;
	EXPORT float CALL_T AxisRange( char * axisId ); // 0 means some error
	// normal output [0 .. AxisRange], though may fall outside this interval. Error: output <= -1000
	EXPORT float CALL_T AxisPosition( char * axisId );
	// value, um. sweepTime, secs, [0..20]
	EXPORT bool CALL_T SetAxisPosition( char * axisId, float * value, float sweepTime );
	EXPORT bool CALL_T SetAxesPositions( int axesCnt, char axesIds[][MAX_AXIS_ID_LEN], float * values, float sweepTime );

	// Unlike the AxisPosition method, this function does not return the current coordinate,
	// but its future value, which will occur at the end of some ongoing procedure in the SPM-software.
	// The method is of need for TCallback procedure imlementation.
	EXPORT float CALL_T AxisSetpoint( char * axisId );

	// Signals list. The function returns signals number, writes signals names and units into "names" and "units" arrays.
	// Since signals number may be about 15-30, declare "names" and "units" as: char names[30][MAX_SIG_NAME_LEN].
	EXPORT int CALL_T SignalsList( char names[][MAX_SIG_NAME_LEN], char units[][MAX_SIG_NAME_LEN] );

	// There are basically 2 scan modes: "line scanning" (or line-scan) and "point scanning" (point-scan).
	// For point-scan, when getting signals, probe XY-velocity is zero, while when transferring between
	// scan points (getting signals points), there are no any measurements performed.
	// Line-scan mode on the opposite implies continuous movement and simultaneous measurements.

	// Every scan procedure starts with
	// SetupScanCommon; TScanMode parameter sets line-scan or point-scan mode.
	// SetupScanLine: first time and then next time before starting new scan line.
	// Then for point-scan call in cycle ExecScanPoint or call ExecScanLine(tpoint); tpoint is dwelling time in scan-points.
	// For line-scan call ExecScanLine(tpoint); tpoint parameter is ignored.

	// It is correctly to end each scan process by call of FinitScan.
	// There is no problem when use ExecScanPoint to stop scan process at any moment.
	// When call ExecScanLine, attempt stops until the line is finished may cause hand on of your software.
	// So, calls of the FinitScan method has to be prepared, see comments above and inside remote_test.cpp module.

	// The function ExecScanPoint moves to the next point of the scan line and return data measured for previous point of the line
	// For the 1st point of the scan line, the ExecScanPoint returns just size = 0
	// For the last point of the line need to call ExecScanPoint two times: to receive the data from previous point and then from last point
	// So, when next ExecScanPoint returns control, you can start to get data from some other external device,
	// while SPM accumulating signals in given scan-point.
	// The ExecScanPoint method implies no triggering. 

	// ExecScanLine call corresponds to getting of all scan-line points.
	// You need to engage your own user-function of type ( *TScanCallback )( int size, float * vals )
	// Across the line user-function will be called asynchronously (i.e. in some separate thread) from time to time, 
	// transferring you the new scanned data via its arguments.
	// If size = 0, it means scan the line is completed.

	// At the begining of the line the scan process pauses small time.
	// Line-scan mode has small over-scan shift out of scan line.
	// Each scan point coordinate is in the center of the interval, where measured data are accumulated.
	// For line-scan tforw argument of the SetupScanLine is equal to the time-interval between starting of the first scanned point and
	// ending of the last scan point.
	// For point-scan tforw is the sum of all time-intervals between scan points.
	// tback sets the time-interval for back (idle) movement when the back displacement is abs equal to the forward displacement,
	// it also defines the time interval when move to first scan point.
	// It is possible to set zero scan area, then some reasonable values for tforw and tback will be chosen automatically.

	// Use SPM-software log-window; you can see them some error-messages (usually in "User log", sometimes in "Full log").

	// Declare "sigs" as char sigs[N][MAX_SIG_NAME_LEN]; N >= sigsCnt
	// !!sigsCnt > 0
	// Triggering (if enabled, see SetTriggering) is executed at the end of the measurement of each scan-point, both for line- and for point-scan.
	// Exception: when use ExecScanPoint function, point trigger is not performed. 
	// One extra trigger is performed at the beginning of the measurement of first point of the line.
	EXPORT bool CALL_T SetupScanCommon( char * planeId, int linePts, TScanMode mode, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );

	EXPORT bool CALL_T SetupScanLine( float x0, float y0, float x1, float y1, float tforw, float tback ); // microns and secs
	EXPORT bool CALL_T ExecScanPoint( int * size, float * vals );
	EXPORT void CALL_T FinitScan();
	EXPORT bool CALL_T ExecScanLine( float tpoint ); // tpoint: time to stay in point [secs], valid only for point-scan

	// SetTriggering function enables/disables a global triggering flag. If flag is on then subsequent operation
	// will be carried out with applying of trigger pulses, if this operation involves such an option.
	EXPORT bool CALL_T SetTriggering( bool enable );

	// Function returns true if only Z-feedback is on, i.e. the probe is on surface
	// also situation, when SenZ signal is Z-feedback input is permissible; it is useful for tests
	// Function uses TScanCallback to send back signals
	// After execution ends the process returns the probe to place, i.e. set Z-feedback to its initial state
	// from, to [nm] - probe displacement from its initial point; positive value means the probe goes up (from the surface)
	// kIdleMove - coefficient to speed up idle parts of the sweep, i.e. from "init" to "from" and from "to" to "init"
	// To break the process call BreakProbeSweepZ(), but!!! at certain moments only
	// see how it is done in remote_test.cpp, CTestForm::sweepZCallback()
	// You may call BreakProbeSweepZ at any moment if only sigsCnt == 0
	EXPORT bool CALL_T ProbeSweepZ( float from, float to, int pts, float sweepT, float kIdleMove, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	EXPORT void CALL_T BreakProbeSweepZ();
	// Function returns true if Z-feedback is on, i.e. the probe is on surface
	// Or when the probe was already lifted, so Z-feedback input is SenZ
	// lift[nm] is from current state, i.e. added to previous lift(s) 
	// if triggering is enabled, first trigger pulse is applied when the probe is just lifted
	// second trigger is applied after triggerTime[sec]
	EXPORT bool CALL_T ProbeLift( float lift, float triggerTime );
	// Function returns true if the probe was first lifted, so Z-feedback input is SenZ
	// Z-feedback input is switched to previous (Mag, Nf, etc.), the same is for other parameters: gain, setpoint
	// land may be too slow if starting from big lifts, say from 1 micron; then it will be possible to rework the function
	// or implement some new
	EXPORT bool CALL_T ProbeLand();

	// Landing width constant and always reasonable value for Z-move rate (unlike in the case of ProbeLand).
	// The method is usefull when start landing from big tip-sample gaps, say, more than 1 micron.
	// When call the function after ProbeLift, it switches the Z-feedback input same as ProbeLand.
	// Otherwise it does not switch Z-feedback input, does not set setpoint and feedback gain.
	EXPORT bool CALL_T ProbeLand2();

	// The "plane-scan" mode is a type of scanning, for which the probe moves in some plane, supposed to be paralell to the sample surface.
	// Here and below, for simplicity, we talk about the motion of the probe, and the sample is assumed to be motionless,
	// although physically for our systems everything happens the other way around.

	// To ensure the movement of the probe in a given plane, for Z-regulation the feedback is used with SenZ-signal
	// (it is the scanner Z-drive position sensor signal) as input. It is necessary to distinguish such feedback from the usual one,
	// which controls the probe-surface gap, and for which the input is some of the "probe" signals - Mag, Nf, Freq, Iprobe.
	// For the feedback which controls the gap we also say that the probe touches the surface or is on the surface. While when SenZ is
	// Z-feedback input, normally Z-control is indifferent to the current probe-surface gap.
	// Although for the plane-scan technique the situation is somewhat different: during scan line trace movement one from the probe
	// signals is also controlled and when the signal shows tip-surface gap becomes too small, the Z-feedback input switches to the signal.
	// When this new Z-feedback control makes the probe to be lower than initial scan-plane level, the feedback input switches back to SenZ.
	// The probe signal and corresponding Z-feedback settings (setpoint, gain), which are used for mentioned extra Z-control,
	// are set automatically when scanning starts.

	// For plane-scan mode it is supposed that the probe-surface gap varies only due to local topography changes under the tip, while
	// mean gap remains constant. But the SPM-system suffers from the probe-surface gap drift, which may pay significant role when
	// the scanning time is big and/or the scanning plane lift is small. So it may be nessesary to correct the scan-plane lift level
	// during scanning.

	// First need to define a set of the surface plane points {x, y, z}. To do this move the probe over the surface to appropriate
	// points: SetAxesPositions(2, {"X", "Y"},..) and get Z-coordinate by and AxisPosition("Z") function.
	// Save the points in 3 arrays corresponding to x, y and z coordinates to transfer the arrays to aist-software later.

	// To prevent any probe lateral moves when it is touching the surface, need to lift it before call
	// next SetAxesPositions(2, {"X", "Y"},..) and land it back to call AxisPosition("Z").
	// For this use ProbeLift and ProbeLand (or ProbeLand2) functions. When operating in such a way, i.e. when no Z-feedback is used
	// to control tip-surface separation, need to lift the probe far enough from the surface before XY-moves.
	// To evaluate the lift value of need, consider the sample surface maximum inclination to be about 4-5 microns per 100 microns
	// in XY-plane and add something related to surface real topography changes.

	// The sequence of functions to start scanning is as follows:
	// SetupPlaneScan, SetPlanePoints, SetPlaneLift, SetupScanLine, ExecScanLine or ExecScanPoint,
	// then everything is as usual (SetupScanLine, ExecScanLine (ExecScanPoint), SetupScanLine, etc.).
	// For point-scan there is no ExecScanLine(tpoint) option.
	// To correct the lift value repeat the AxisPosition("Z") at some one from XY points used previously. Do this
	// between scan-lines:
	// ...ExecScanLine (or last ExecScanPoint of the line), ProbeLand, SetAxesPositions, AxisPosition, ProbeLift, SetupScanLine.

	// Before start of scanning, i.e. before call of first ExecScanLine (ExecScanPoint), call ProbeLift. The lift value does not matter.
	// Each scan-line finishes when the probe is lifted, the lift value is "lift" + "liftback" (see SetPlaneLift).
	// So after scanning, to switch the Z-control back from SenZ to the probe-signal call ProbeLand.

	// Warning! Plane-scan mode from remote_test.exe is valid only for 1st feedback signal (probe-signal) is SenZ. To run the method,
	// remove the probe by Z-motor far enough from the sample, choose SenZ as Z-feedback input, enable Z-feedback
	// and set Z-scanner to be somewhere close to its middle position by tuning the setpoint.

	EXPORT bool CALL_T SetupPlaneScan( int linePts, TScanMode mode, int sigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	// Due to the design of the scanner, in order to ensure the movement of the probe in the plane, special Z-control is required.
	// Therefore, it is necessary to transfer to aist-software the original coordinates of the points of the surface, and not,
	// say, the direct equation of the plane, or the Z-coordinates of the beginning and end of the scan-line.
	EXPORT bool CALL_T SetPlanePoints( int ptsCnt, float * x, float * y, float * z );
	// Set lift, liftback in nm. During back-movement the lift over the surface plane is the sum of the "lift" and "liftback" values.
	EXPORT void CALL_T SetPlaneLift( float lift, float liftback ); // nm, nm

	// "2pass" scanning start:
	// SetupScan2Pass, Set2PassLift, Set2PassTriggering (for line-scan), Setup2PassLine, ExecScanLine or ExecScanPoint.
	// For point-scan there is no ExecScanLine(tpoint) option.

	// For line-scan pass1 and pass2 are pefromed in the same (trace) direction; there are two retrace idle movements, performed
	// after pass1 and pass2. The retrace moves have additional (relatively to pass2) lift-value = "liftback";
	// the time for retrace movement is set by tpass2back, which supposed to be small.
	// For line-scan TScanCallback function reseives all data for the scan-point, i.e. all sigsCnt values in one portion. That's why
	// the scanned data begin to flow only after the start of pass2. The consequence of this is that during scan-line execution 
	// finitScan method may be called only when pass2 is on.

	// For point-scan pass2 is performed in retrace direction; there are no idle movements: "tpass2back" and "liftback" parameters
	// are not used. ExecScanPoint returns scanned data for pass2 in reversed order,
	// i.e. first returned point corresponds to last point of the scan-line.

	// The "sigs" contains signals names both for first and for second pass. First pass1SigsCnt names are for the first pass.
	EXPORT bool CALL_T SetupScan2Pass( int linePts, TScanMode mode, int sigsCnt, int pass1SigsCnt, char sigs[][MAX_SIG_NAME_LEN] );
	// um and secs. tpass2back is a time for 2 retrace idle movements per scan-line, which are performed
	// when the probe is lifted ("lift" + "liftback").
	EXPORT bool CALL_T Setup2PassLine( float x0, float y0, float x1, float y1, float tpass1, float tpass2, float tpass2back );
	// Set lift, liftback in nm. During back-movement the lift over the surface plane is the sum of the "lift" and "liftback" values.
	EXPORT void CALL_T Set2PassLift( float lift, float liftback ); // nm, nm
	// The SetTriggering method is not valid for 2pass scanning. Use this function instead.
	EXPORT void CALL_T Set2PassTriggering( bool pass1On, bool pass2On );

}







