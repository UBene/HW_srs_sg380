#include "remote_test_lib.h"
#include <QDebug>
#include <QStringList>

CRemoteCtrl::CRemoteCtrl( const QString & folderName, QObject * parent )
	: QObject( parent )
{
	m_lib = new QLibrary(folderName + "/remote_spm.dll", this);
	if (!m_lib->load()) {
		m_resolveError = "Library " + folderName + "/remote_spm.dll" + " was NOT loaded";
		return;
	}

	QStringList errors;
	bool resolved = true;

	initialization = (TInitialization)m_lib->resolve("Initialization");
	if (!initialization) 
		{ errors << "\"Initialization\" was not resolved"; resolved = false; }

	finalization = (TFinalization)m_lib->resolve("Finalization");
	if (!finalization) 
		{ errors << "\"Fnitialization\" was not resolved"; resolved = false; }

	isConnected	= (TIsConnected)m_lib->resolve("IsConnected");
	if (!isConnected) 
		{ errors << "\"IsConnected\" was not resolved"; resolved = false; }

	sendLogMessage = (TSendLogMessage)m_lib->resolve("SendLogMessage");
	if (!sendLogMessage)
		{ errors << "\"SendLogMessage\" was not resolved"; resolved = false; }

	initTestCallback = (TInitTestCallback)m_lib->resolve("InitTestCallback");
	if (!initTestCallback) 
		{ errors << "\"InitTestCallback\" was not resolved"; resolved = false; }
	
	initTestScanCallback = (TInitTestScanCallback)m_lib->resolve("InitTestScanCallback");
	if (!initTestScanCallback) 
		{ "errors << \"InitTestScanCallback\" was not resolved"; resolved = false; }

	setCallback = (TSetCallback)m_lib->resolve("SetCallback");
	if (!setCallback) 
		{ errors << "\"SetCallback\" was not resolved"; resolved = false; }

	setScanCallback	= (TSetScanCallback)m_lib->resolve("SetScanCallback");
	if (!setScanCallback) 
		{ errors << "\"SetScanCallback\" was not resolved"; resolved = false; }

	setRestartLineCallback = (TSetRestartLineCallback)m_lib->resolve("SetRestartLineCallback");

	serverInterfaceVersion = (TServerInterfaceVersion)m_lib->resolve("ServerInterfaceVersion");
	clientInterfaceVersion = (TClientInterfaceVersion)m_lib->resolve("ClientInterfaceVersion");
	isServerCompatible = (TIsServerCompatible)m_lib->resolve("IsServerCompatible");

	axisRange = (TAxisRange)m_lib->resolve("AxisRange");
	if (!axisRange) 
		{ errors << "\"AxisRange\" was not resolved"; resolved = false; }

	axisPosition = (TAxisPosition)m_lib->resolve("AxisPosition");
	setAxisPosition = (TSetAxisPosition)m_lib->resolve("SetAxisPosition");
	setAxesPositions = (TSetAxesPositions)m_lib->resolve("SetAxesPositions");
	axisSetpoint = (TAxisSetpoint)m_lib->resolve("AxisSetpoint");

	signalsList = (TSignalsList)m_lib->resolve("SignalsList");
	setupScanCommon = (TSetupScanCommon)m_lib->resolve("SetupScanCommon");
	setupScanLine = (TSetupScanLine)m_lib->resolve("SetupScanLine");
	execScanPoint = (TExecScanPoint)m_lib->resolve("ExecScanPoint");
	finitScan = (TFinitScan)m_lib->resolve("FinitScan");
	execScanLine = (TExecScanLine)m_lib->resolve("ExecScanLine");
	setTriggering = (TSetTriggering)m_lib->resolve("SetTriggering");

	probeSweepZ = (TProbeSweepZ)m_lib->resolve("ProbeSweepZ");
	breakProbeSweepZ = (TBreakProbeSweepZ)m_lib->resolve("BreakProbeSweepZ");
	probeLift = (TProbeLift)m_lib->resolve("ProbeLift");
	probeLand = (TProbeLand)m_lib->resolve("ProbeLand");
	probeLand2 = (TProbeLand2)m_lib->resolve("ProbeLand2");

	setupPlaneScan = (TSetupPlaneScan)m_lib->resolve("SetupPlaneScan");
	setPlanePoints = (TSetPlanePoints)m_lib->resolve("SetPlanePoints");
	setPlaneLift = (TSetPlaneLift)m_lib->resolve("SetPlaneLift");

	setupScan2Pass = (TSetupScan2Pass)m_lib->resolve("SetupScan2Pass");;
	setup2PassLine = (TSetup2PassLine)m_lib->resolve("Setup2PassLine");
	set2PassLift = (TSet2PassLift)m_lib->resolve("Set2PassLift");
	set2PassTriggering = (TSet2PassTriggering)m_lib->resolve("Set2PassTriggering");

	if ( !resolved ) {
		m_resolveError = errors[0];
		for (int i = 1; i < errors.size(); i++ )
			m_resolveError.append(QString("\n%1").arg(errors[i]));
		m_lib->unload();
	}
}

bool CRemoteCtrl::isLoaded()
{
	return m_lib->isLoaded();
}

const QString & CRemoteCtrl::resolveError()
{
	return m_resolveError;
}

