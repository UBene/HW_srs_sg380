#include "remote_test.h"
#include "remote_test_lib.h"

CTestForm::CTestForm( QWidget * p )
	: QWidget(p), paramSemaphore(1)
{
	m_lib = new CRemoteCtrl("remote_spm", this);
	m_initialized = false;

	QHBoxLayout * mainLay = new QHBoxLayout(this);
	QVBoxLayout * panelLay = new QVBoxLayout; mainLay->addLayout(panelLay);
	panelLay->setSpacing(3);

	m_log = new QPlainTextEdit; mainLay->addWidget(m_log, 1);

	QPushButton * checkScanCallbackBtn = new QPushButton("Check ScanCallback");
	QSize btn_sz = checkScanCallbackBtn->sizeHint(); btn_sz.setWidth(btn_sz.width()+8);

	QPushButton * initBtn = new QPushButton("Connect");
	initBtn->setFixedSize(btn_sz);
	panelLay->addWidget(initBtn, 0, Qt::AlignLeft);
	connect(initBtn, SIGNAL(clicked()), SLOT(init()) );

	QPushButton * logBtn = new QPushButton("Send message");
	logBtn->setFixedSize(btn_sz);
	panelLay->addWidget(logBtn, 0, Qt::AlignLeft);
	connect(logBtn, SIGNAL(clicked()), SLOT(sendMessage()) );

	m_sendMsgEdit = new QLineEdit; panelLay->addWidget(m_sendMsgEdit);
	m_sendMsgEdit->setText("Test message 12345");

	int W = m_sendMsgEdit->sizeHint().width();
	if (W < btn_sz.width() + 30 + 2) {
		W = btn_sz.width() + 30 + 2;
		m_sendMsgEdit->setFixedWidth(W);
	}

	panelLay->addSpacing(5);

	QPushButton * checkCallbackBtn = new QPushButton("Check Callback");
	checkCallbackBtn->setFixedSize(btn_sz);
	panelLay->addWidget(checkCallbackBtn, 0, Qt::AlignLeft);
	connect(checkCallbackBtn, SIGNAL(clicked()), SLOT(checkCallback()) );

	checkScanCallbackBtn->setFixedSize(btn_sz);
	panelLay->addWidget(checkScanCallbackBtn, 0, Qt::AlignLeft);
	connect(checkScanCallbackBtn, SIGNAL(clicked()), SLOT(checkScanCallback()) );

	panelLay->addSpacing(8);

	QHBoxLayout * hl = new QHBoxLayout; panelLay->addLayout(hl); hl->setSpacing(2);
	QPushButton * scnRngBtn = new QPushButton("Axis Range");
	scnRngBtn->setFixedSize(btn_sz);
	hl->addWidget(scnRngBtn);//, 1);
	connect(scnRngBtn, SIGNAL(clicked()), SLOT(axisRange()) );

	m_scnRngEdit = new QLineEdit; hl->addWidget(m_scnRngEdit);
	m_scnRngEdit->setFixedWidth(W - btn_sz.width() - 2);
	m_scnRngEdit->setText("X");

	QPushButton * sigsListBtn = new QPushButton("Signals List");
	sigsListBtn->setFixedSize(btn_sz);
	panelLay->addWidget(sigsListBtn, 0, Qt::AlignLeft);
	connect(sigsListBtn, SIGNAL(clicked()), SLOT(signalsList()) );

	panelLay->addSpacing(8);

	m_scanBtn = new QPushButton("Scan"); m_scanBtn->setCheckable(true);
	connect(m_scanBtn, SIGNAL(clicked()), SLOT(onScanBtn()) );
	m_scanTypeCb = new QComboBox;
	m_scanTypeCb->addItem("Point"); m_scanTypeCb->addItem("Line");
	m_planeIdCb = new QComboBox;
	QStringList list; list << "XY" << "XZ" << "YZ" << "X2Y2" << "X2Z2" << "Y2Z2" << "Plane" << "2Pass";
	m_planeIdCb->addItems(list);

	m_ptTriggerChB = new QCheckBox;
	m_ptTriggerChB->setText("Triggering");
	connect(m_ptTriggerChB, SIGNAL(clicked()), SLOT(setTriggering()));

	hl = new QHBoxLayout; panelLay->addLayout(hl); hl->setSpacing(0);
	hl->addWidget(m_scanBtn, 1); hl->addWidget(m_scanTypeCb);

	hl = new QHBoxLayout; panelLay->addLayout(hl); hl->setSpacing(0);
	hl->addWidget(m_ptTriggerChB); hl->addStretch(); hl->addWidget(m_planeIdCb);
	m_planeIdCb->setFixedWidth(m_scanTypeCb->sizeHint().width() + 3);
	m_scanTypeCb->setFixedWidth(m_scanTypeCb->sizeHint().width() + 3);

	panelLay->addSpacing(4);

	m_sweepZBtn = new QPushButton("Sweep Z"); m_sweepZBtn->setCheckable(true);
	connect(m_sweepZBtn, SIGNAL(clicked(bool)), SLOT(onSweepZBtn()) );
	m_sweepFrom = new QDoubleSpinBox;
	m_sweepFrom->setSuffix(" nm"); m_sweepFrom->setRange(-5000, 5000);
	m_sweepFrom->setDecimals(0); m_sweepFrom->setValue(30);
	m_sweepTo = new QDoubleSpinBox;
	m_sweepTo->setSuffix(" nm"); m_sweepTo->setRange(-5000, 5000);
	m_sweepTo->setDecimals(0); m_sweepTo->setValue(-3);
	QPushButton * m_liftBtn = new QPushButton("Lift");
	connect(m_liftBtn, SIGNAL(clicked()), SLOT(onLiftBtn()) );
	QPushButton * m_landBtn = new QPushButton("Land");
	connect(m_landBtn, SIGNAL(clicked()), SLOT(onLandBtn()) );

	//m_sweepZBtn->setFixedSize(btn_sz);
	hl = new QHBoxLayout; panelLay->addLayout(hl); hl->setSpacing(2);
	hl->addWidget(m_sweepZBtn, 0, Qt::AlignCenter);
	QVBoxLayout * vl = new QVBoxLayout; hl->addLayout(vl); vl->setSpacing(2);
	vl->addWidget(m_sweepFrom); vl->addWidget(m_sweepTo);
	hl = new QHBoxLayout; panelLay->addLayout(hl); hl->setSpacing(0);
	hl->addWidget(m_liftBtn); hl->addWidget(m_landBtn);

	panelLay->addSpacing(8);

	int w05 = qRound((W-2.) * 0.5);

	m_setAxesPosBtn = new QPushButton("Set axes"); m_setAxesPosBtn->setCheckable(true);
	m_setAxesPosBtn->setFixedWidth(w05);
	connect(m_setAxesPosBtn, SIGNAL(clicked()), SLOT(onAxesPosBtn()) );
	m_axesPosCb = new QComboBox;
	list.clear(); list << " X" << " Y" << " Z" << " X Y" << " X Z" << " Y Z" << " X Y Z"
					<< " X2" << " Y2" << " Z2" << " X2 Y2" << " X2 Z2" << " Y2 Z2" << " X2 Y2 Z2";
	m_axesPosCb->addItems(list);
	connect(m_axesPosCb, SIGNAL(currentIndexChanged(int)), SLOT(onAxesPosCb()) );
	for(int i = 0; i < 3; i++) {
		QDoubleSpinBox * spin = new QDoubleSpinBox; spin->setSuffix(" µm");
		spin->setRange(-50, 150); spin->setDecimals(2);
		spin->setFixedWidth(w05);
		m_axesPosSpins << spin;
	}
	m_axesPosTimeSb = new QDoubleSpinBox; m_axesPosTimeSb->setSuffix(" sec");
	m_axesPosTimeSb->setRange(0, 20); m_axesPosTimeSb->setDecimals(2);

	QGridLayout * gl = new QGridLayout; panelLay->addLayout(gl);
	gl->setHorizontalSpacing(W - 2*w05);
	gl->addWidget(m_setAxesPosBtn, 0, 0); gl->addWidget(m_axesPosCb, 1, 0); gl->addWidget(m_axesPosTimeSb, 2, 0);
	gl->addWidget(m_axesPosSpins[0], 0, 1); gl->addWidget(m_axesPosSpins[1], 1, 1); gl->addWidget(m_axesPosSpins[2], 2, 1);
	m_axesPosSpins[1]->setVisible(false); m_axesPosSpins[2]->setVisible(false);

	panelLay->addStretch();

	connect(this, SIGNAL(sigLog(const QString &)), SLOT(slotLog(const QString &)) );
	connect(this, SIGNAL(sigScanCallback()), SLOT(scanCallback()) );
	connect(this, SIGNAL(sigCallback(int)), SLOT(callback(int)) );
	connect(this, SIGNAL(sigRestartLineCallback()), SLOT(restartLineCallback()) );
	connect(this, SIGNAL(sigSweepZCallback()), SLOT(sweepZCallback()) );
	
	if (m_lib->isLoaded())
		init();
	else {
		m_log->appendPlainText(m_lib->resolveError());
		m_lib->deleteLater();
	}
	m_scanstopped = true;
}

CTestForm * test_form = 0;


CTestForm::~CTestForm()
{
	if ( m_initialized )
		m_lib->finalization();
}

void CTestForm::emitLog( const QString & stri )
{
	emit sigLog(stri);
}

// ******** Next checkCallback (of type TCallback) and checkScanCallback (of type TScanCallback) functions
// are to premiliary familiarize with the library utilizing. No real SPM-system is of need.
void checkCallback( int proc_index )
{
	if ( !test_form )
		return;
	QString stri = QString("checkCallback proc_index %1").arg(proc_index);
	test_form->emitLog(stri);
}
void checkScanCallback( int size, float * vals )
{
	if ( !test_form )
		return;
	QString stri = QString("checkScanCallBack: size %1, vals").arg(size);
	for ( int i = 0; i < size; i++ )
		stri.append(QString(" %1").arg(vals[i], 3, 'f', 2, '0'));
	test_form->emitLog(stri);
}


void CTestForm::slotLog( const QString & stri )
{
	m_log->appendPlainText( QString("%1").arg( stri ) );
	//m_log->verticalScrollBar()->setValue( ui.msgEdt->verticalScrollBar()->maximum() );
}

// TCallback function header
void callback( int proc_index );

void CTestForm::init()
{
	if (!m_lib)
		return;
	if (m_initialized)
		m_lib->finalization();

	m_lib->initialization();
	bool res = m_lib->isConnected();
	m_log->appendPlainText(res ? "Connected" : QString("Failed to connect"));
	if ( !res )
		m_lib->finalization();

	setWindowTitle(res ? "connected" : "Not connected");
	m_initialized = res;
	if ( res )
		test_form = this;
	onAxesPosCb();
	if (m_initialized) {
		m_lib->setCallback(::callback);

		m_log->appendPlainText(tr("Server Interface Version\t%1").arg(m_lib->serverInterfaceVersion()));
		m_log->appendPlainText(tr("Client Interface Version \t%1").arg(m_lib->clientInterfaceVersion()));
		m_log->appendPlainText(tr("Client and Server versions compatible: %1")
			.arg((m_lib->isServerCompatible()) ? "Yes" : "No"));
	}
}

void CTestForm::sendMessage()
{
	if (m_initialized) {
		char response[128];
		m_lib->sendLogMessage(m_sendMsgEdit->text().toLatin1().data(), response);
		m_log->appendPlainText(response);
	}
}

void CTestForm::checkCallback()
{
	if (m_initialized) {
		m_lib->setCallback(::checkCallback);
		m_lib->initTestCallback();
	}
}

void CTestForm::checkScanCallback()
{
	if (m_initialized) {
		m_lib->setScanCallback(::checkScanCallback);
		m_lib->initTestScanCallback();
	}
}

void CTestForm::axisRange()
{
	if (m_initialized) {
		QString axisId = m_scnRngEdit->text();
		float res = m_lib->axisRange(axisId.toLatin1().data());
		m_log->appendPlainText(QString("Axis Range %1 %2").arg(axisId).arg(res));
	}
}

void CTestForm::signalsList()
{
	if (!m_initialized) return;
	char names[30][MAX_SIG_NAME_LEN], units[30][MAX_SIG_NAME_LEN];
	int sigsCnt = m_lib->signalsList(names, units);
	if (sigsCnt > 0) {
		m_log->appendPlainText(tr("signalsList length = %1").arg(sigsCnt));
		for (int sigInd = 0; sigInd < sigsCnt; sigInd++)
			m_log->appendPlainText(QString("%1   %2").arg(names[sigInd]).arg(units[sigInd]));
	}
	else
		m_log->appendPlainText("Signals List failed");

}

void CTestForm::mysleep( int tsleep )
{
	QTime t;
	t.start();
	do {
		QApplication::processEvents();
	} while (t.elapsed() < tsleep);
}

// TScanCallback function to be registered via SetScanCallback, see remote_spm.h
void scanCallback( int size, float * vals )
{
	//qDebug() << "scanCallback thread" << QThread::currentThreadId();
	if (test_form)
		test_form->emitScanCallback(size, vals);
}
// TScanCallback function to be registered via SetScanCallback, see remote_spm.h
void sweepZCallback( int size, float * vals )
{
	if (test_form)
		test_form->emitSweepZCallback(size, vals);
}

// TRestartLineCallback function to be registered via SetRestartLineCallback, see remote_spm.h
void restartLineCallback()
{
	if (test_form)
		test_form->emitRestartLineCallback();
}

// TScanCallback function realization.
// paramLock() .. paramWaitUnlock() construction stops the caller-thread, until data will be transferred
// to CTestForm::scanCallback(), which is run inside main thread.
// Use of m_scanstopped flag is for processing situation, when user stops scanning,
// while current scan-line is not completed.
// First purpose of the flag is to prevent engaging of the CTestForm::scanCallback() method two times. 
// Secondly, it prevents blocking of the caller-thread (paramLock()) somewhere at the moment,
// when FinitScan method is called in main thread from CTestForm::scanCallback() method.
void CTestForm::emitScanCallback( int size, float * vals )
{
	if (m_scanstopped)
		return;
	paramLock();
	scanPars.vals.resize(size);
	for (int i = 0; i < size; i++)
		scanPars.vals[i] = vals[i];
	emit sigScanCallback();
	paramWaitUnlock();
}

// The slot-method engaged by CTestForm::emitScanCallback
void CTestForm::scanCallback()
{
	// Check user-stop; enable m_scanstopped flag before any other actions
	m_scanstopped = (!m_scanBtn->isChecked());
	
	// recieve scannes data
	int sz = scanPars.vals.size();
	if (sz){
		int npts = sz/scanPars.sigsCnt;
		//qDebug() << "npts" << npts << " scanPars.vals.size()" << sz << " sigsCnt" << scanPars.sigsCnt;
		QString stri = QString("L%1  add scanned pts %2").arg(scanPars.line).arg(npts);
		for ( int i = 0; i < sz; i++ )
			stri.append(QString("   %1").arg((int)scanPars.vals[i]));
		m_log->appendPlainText(stri);
		// If not user-stop, release the TScanCallback-function caller thread and return
		if (!m_scanstopped) {
			paramUnlock();
			return;
		}
	}

	// Was user-stop: obtained data size (sz) maybe zero or not; release the TScanCallback-function caller thread,
	// call FinitScan, then return
	if (m_scanstopped) {
		paramUnlock();
		m_lib->finitScan();
		m_log->appendPlainText("CTestForm::scanCallback Scan process was stopped by user.");
		return;
	}

	// Obtained data size (sz) is zero; incrementing scan-line index
	scanPars.line++;
	if (scanPars.line <= scanPars.linesCnt) {
	// Release the TScanCallback-function caller thread, then call execScanLine()
		paramUnlock();
		m_log->appendPlainText("Scan line finished. Starting new...\n");
		execScanLine();
	}
	else {
	// Scan process completed: release the TScanCallback-function caller thread, then call FinitScan
		m_scanstopped = true;
		paramUnlock();
		m_lib->finitScan();
		m_scanBtn->setChecked(false);
		m_log->appendPlainText("Scan line finished. Scan process finished\n");
	}

}

void CTestForm::emitRestartLineCallback()
{
	emit sigRestartLineCallback();
}

void CTestForm::restartLineCallback()
{
	m_log->appendPlainText("***********Restart line call back");
}

bool CTestForm::setupScanCommon()
{
	QString axisId1("X"), axisId2("Y");
	scanPars.xyz = false; scanPars.pass2 = false;
	QString planeId = m_planeIdCb->currentText();
	if (planeId == "XY") { axisId1 = "X"; axisId2 = "Y"; }
	else if (planeId == "XZ") { axisId1 = "X"; axisId2 = "Z"; }
	else if (planeId == "YZ") { axisId1 = "Y"; axisId2 = "Z"; }
	else if (planeId == "X2Y2") { axisId1 = "X2"; axisId2 = "Y2"; }
	else if (planeId == "X2Z2") { axisId1 = "X2"; axisId2 = "Z2"; }
	else if (planeId == "Y2Z2") { axisId1 = "Y2"; axisId2 = "Z2"; }
	else if (planeId == "Plane") { scanPars.xyz = true; }
	else if (planeId == "2Pass") { scanPars.pass2 = true; }

	scanPars.sigsCnt = 3;
	char sigs[10][MAX_SIG_NAME_LEN];
	strcpy(sigs[0], tr("Sen%1").arg(axisId1).toLatin1().data());
	strcpy(sigs[1], tr("Sen%1").arg(axisId2).toLatin1().data());
	strcpy(sigs[2], tr("Nf").toLatin1().data());

	if (scanPars.pass2) {
		scanPars.sigsCnt = 5;
		strcpy(sigs[2], tr("SenZ").toLatin1().data());
		strcpy(sigs[3], tr("SenX").toLatin1().data());
		strcpy(sigs[4], tr("SenZ").toLatin1().data());
	}

	float range1 = m_lib->axisRange(axisId1.toLatin1().data());
	float range2 = m_lib->axisRange(axisId2.toLatin1().data());
	float range3 = (scanPars.xyz) ? m_lib->axisRange("Z") : 0;

	if (range1 == 0 || range2 == 0) {
		m_log->appendPlainText(tr("Error. Scanner range1 = %1, range2 = %2\nOperation aborted.")
									.arg((int)range1).arg((int)range2));
		return false;
	}
	bool point = (m_scanTypeCb->currentText() == "Point");
	scanPars.linePts = (point) ? 6 : 200; scanPars.linesCnt = 4;
	if (scanPars.pass2 && point) scanPars.linePts = 20; 
	scanPars.X0 = 0.45 * range1; scanPars.Y0 = 0.25 * range2;
	scanPars.W = 0.1 * range1; scanPars.H = 0.5 * range2;
	if (scanPars.pass2) { scanPars.W = 0.3 * range1; scanPars.H = 0.3 * range2; }
	scanPars.tforw = ( scanPars.W == 0 ) ? 0 : 3;
	scanPars.tback = ( scanPars.W == 0 ) ? 0 : 0.3;

	QString stri = tr("Init scan proc, (X, Y, W, H) = {%1, %2, %3, %4}\nlinePts = %5, lines = %6\n")
			.arg(scanPars.X0).arg(scanPars.Y0).arg(scanPars.W).arg(scanPars.H)
			.arg(scanPars.linePts).arg(scanPars.linesCnt);

	if (scanPars.pass2) {
		scanPars.tpass1 = 1;
		scanPars.tpass2 = 2;
		scanPars.tpass2back = 0.5;
		m_log->appendPlainText(stri + tr("tpass1 = %1, tpass2 = %2, tpass2back = %3\n" 
			"Signals: %4  %5  %6\nSignals 2nd pass: %7  %8")
			.arg(scanPars.tpass1).arg(scanPars.tpass2).arg(scanPars.tpass2back)
			.arg(sigs[0]).arg(sigs[1]).arg(sigs[2]).arg(sigs[3]).arg(sigs[4]));
	}
	else
		m_log->appendPlainText(stri + tr("tforw = %1, tback = %2\nSignals: %3  %4  %5")
				.arg(scanPars.tforw).arg(scanPars.tback).arg(sigs[0]).arg(sigs[1]).arg(sigs[2]));
	mysleep(0);

	scanPars.procScanPoints = point && (!m_ptTriggerChB->isChecked());
	if (scanPars.xyz || scanPars.pass2)
		scanPars.procScanPoints = point;
	scanPars.tpoint = (point) ? 0.2 : 0; // 0.2 sec
	TScanMode mode = (point) ? POINT_SCAN : LINE_SCAN;

	if (scanPars.xyz) {
		if (!m_lib->setupPlaneScan(scanPars.linePts, mode, scanPars.sigsCnt, sigs))
			return false;
		float X[4] = {scanPars.X0, scanPars.X0, scanPars.X0 + scanPars.W, scanPars.X0 + scanPars.W};
		float Y[4] = {scanPars.Y0, scanPars.Y0 + scanPars.H, scanPars.Y0, scanPars.Y0 + scanPars.H};
		float Z[4] = {0.3 * range3, 0.5 * range3, 0.5 * range3, 0.6 * range3};
		if (!m_lib->setPlanePoints(4, X, Y, Z))
			return false;
		m_lib->setPlaneLift(1000, 1000);
	}
	else if (scanPars.pass2) {
		if (!m_lib->setupScan2Pass(scanPars.linePts, mode, scanPars.sigsCnt, 3, sigs))
			return false;
		m_lib->set2PassLift(500, 500);
		m_lib->set2PassTriggering(m_ptTriggerChB->isChecked(), m_ptTriggerChB->isChecked());
	}
	else if (!m_lib->setupScanCommon(planeId.toLatin1().data(), scanPars.linePts, mode, scanPars.sigsCnt, sigs)) {
		m_log->appendPlainText("Error. setupScanCommon failed.");
		m_scanBtn->setChecked(false);
		return false;
	}
	//qDebug() << "after setupScanCommon" << time.elapsed(); time.restart();

	scanPars.stepx = scanPars.W/(scanPars.linePts-1.);
	scanPars.stepy = scanPars.H/(scanPars.linesCnt-1.);

	return true;
}

void CTestForm::procScanPoints()
{
	int line = 0;
	while (line < scanPars.linesCnt) {
RestartLine:
		float x0 = scanPars.X0, y0 = scanPars.Y0 + scanPars.stepy * line;
		float x1 = scanPars.X0 + scanPars.W, y1 = y0;
		bool res = (scanPars.pass2) ? m_lib->setup2PassLine(x0, y0, x1, y1, scanPars.tpass1, scanPars.tpass2, scanPars.tpass2back)
								: m_lib->setupScanLine(x0, y0, x1, y1, scanPars.tforw, scanPars.tback);
		if (!res) {
			m_log->appendPlainText("Error. setupScanLine failed.");
			m_scanBtn->setChecked(false);
			return;
		}
		int size; float vals[10];
		int line_pts_sz = (scanPars.pass2) ? 2*scanPars.linePts + 1 : scanPars.linePts + 1;
		int pt_ind, pass_ind;
		for (int pt = 0; pt < line_pts_sz; pt++) {
			if (scanPars.pass2) {
				if (pt > scanPars.linePts) {
					pass_ind = 2;
					pt_ind = line_pts_sz - 1 - pt;
				}
				else {
					pt_ind = pt;
					pass_ind = 1;
				}
			}
			if (!m_lib->execScanPoint(&size, vals)) {
				if (scanPars.pass2)
					m_log->appendPlainText(tr("Error. execScanPoint failed pt %1 (pass %2), restarting line %3")
											.arg(pt_ind).arg(pass_ind).arg(line));
				else
					m_log->appendPlainText(tr("Error. execScanPoint failed pt %1, restarting line %2").arg(pt).arg(line));
				mysleep(100);
				if (!m_scanBtn->isChecked()) {
					m_lib->finitScan();
					m_log->appendPlainText("CTestForm::procScanPoints Scan process was stopped by user.");
					return;
				}
				goto RestartLine;
			}
			else {
				QString s = tr("L%1").arg(line+1);
				if (pt == 0)
					s.prepend('\n').append(" started");
				else {
					if (scanPars.pass2)
						s += tr(" pt%1 (pass %2)").arg(pt_ind).arg(pass_ind);
					else
						s += tr(" pt%1").arg(pt);
				}
				if (size) {
					for (int i = 0; i < size; i++)
						s += "   " + QString::number(vals[i]);
				}
				m_log->appendPlainText(s);
			}
			mysleep(100);
			if (!m_scanBtn->isChecked()) {
				m_lib->finitScan();
				m_log->appendPlainText("CTestForm::procScanPoints Scan process was stopped by user.");
				return;
			}
		}
		line++;
	}
	m_lib->finitScan();
	m_scanBtn->setChecked(false);
	m_log->appendPlainText("CTestForm::procScanPoints. Scan process finished\n");
}

void CTestForm::execScanLine()
{
	float x0 = scanPars.X0, y0 = scanPars.Y0 + scanPars.stepy * (scanPars.line - 1);
	float x1 = scanPars.X0 + scanPars.W, y1 = y0;
	bool res = (scanPars.pass2) ? m_lib->setup2PassLine(x0, y0, x1, y1, scanPars.tpass1, scanPars.tpass2, scanPars.tpass2back)
								: m_lib->setupScanLine(x0, y0, x1, y1, scanPars.tforw, scanPars.tback);
	if (!res) {
		m_log->appendPlainText("Error. setupScanLine failed.");
		m_scanBtn->setChecked(false);
		return;
	}

	if (scanPars.line == 1) {
		m_lib->setScanCallback(::scanCallback);
		m_lib->setRestartLineCallback(::restartLineCallback);
	}
	if (!m_lib->execScanLine(scanPars.tpoint)) {
		m_log->appendPlainText(tr("Error. execScanLine %1 failed.").arg(scanPars.line));
		m_scanBtn->setChecked(false);
	}
}

void CTestForm::onScanBtn()
{
	if (!m_scanBtn->isChecked()) // Do not call here FinitScan
		return;

	m_scanstopped = false;
	if (!setupScanCommon()) {
		m_scanBtn->setChecked(false);
		return;
	}
	if (scanPars.procScanPoints)
		procScanPoints();
	else {
		scanPars.line = 1;
		execScanLine();
	}
}

// TCallback function which is called in axiluary thread engages CTestForm::callback called in main thread
void callback( int proc_index )
{
	if (test_form)
		test_form->emitCallback(proc_index);
}

void CTestForm::emitCallback( int proc_index )
{
	emit sigCallback(proc_index);
}

void CTestForm::callback( int proc_index )
{
	QString txt = m_axesPosCb->currentText();
	QStringList list = txt.split(" ", QString::SkipEmptyParts);
	int scnInd = ( list.contains("X") || list.contains("Y") || list.contains("Z") ) ? 1 : 2;
	if (scnInd != proc_index)
		return;
	for(int i = 0; i < list.size(); i++) {
		float res = m_lib->axisSetpoint(list[i].toLatin1().data());
		if (res <= -1000)
			m_log->appendPlainText(tr("AxisSetpoint %1 failed").arg(list[i]));
		else
			m_axesPosSpins[i]->setValue(res);
	}
}

void CTestForm::onAxesPosBtn()
{
	if (!m_setAxesPosBtn->isChecked())
		return;
	char axesIds[3][MAX_AXIS_ID_LEN];
	QString txt = m_axesPosCb->currentText();
	QStringList list = txt.split(" ", QString::SkipEmptyParts);
	qDebug() << list;
	QVector<float> values;
	for (int i = 0; i < list.size(); i++)
		values << (float)m_axesPosSpins[i]->value();
	float sweepTime = (float)m_axesPosTimeSb->value();
	if (list.size() == 1) {
		if (m_lib->setAxisPosition(list[0].toLatin1().data(), values.data(), sweepTime)) {
			m_axesPosSpins[0]->setValue(values[0]);
			m_log->appendPlainText(tr("SetAxisPosition %1 to %2 finished").arg(list[0]).arg(values[0], 0, 'f', 2));
		}
		else
			m_log->appendPlainText(tr("SetAxisPosition %1 to %2 FAILED").arg(list[0]).arg(values[0], 0, 'f', 2));
	}
	else {
		for (int i = 0; i < list.size(); i++)
			strcpy(axesIds[i], list[i].toLatin1().data());

		qDebug() << axesIds[0] << axesIds[1] << list[0].toLatin1().data() << list[1].toLatin1().data();
//		qDebug() << std::string(axesIds[0]) << std::string(axesIds[1]);

		bool res = m_lib->setAxesPositions(list.size(), axesIds, values.data(), sweepTime);
		if (res) {
			for (int i = 0; i < list.size(); i++)
				m_axesPosSpins[i]->setValue(values[i]);
		}
		
		QString str("SetAxesPositions");
		for (int i = 0; i < list.size(); i++)
			str += " " + list[i];
		str += " to";
		for (int i = 0; i < list.size(); i++)
			str += tr(" %1").arg(values[i], 0, 'f', 2);
		if (res)
			str += " finished";
		else
			str += " FAILED";
		m_log->appendPlainText(str);
	}
	m_setAxesPosBtn->setChecked(false);
}

void CTestForm::onAxesPosCb()
{
	QString txt = m_axesPosCb->currentText();
	QStringList list = txt.split(" ", QString::SkipEmptyParts);
	//qDebug() << list;
	for(int i = 0; i < 3; i++)
		m_axesPosSpins[i]->setVisible(i < list.size());
	if (m_initialized) {
		for(int i = 0; i < list.size(); i++) {
			float res = m_lib->axisPosition(list[i].toLatin1().data());
			if (res <= -1000)
				m_log->appendPlainText(tr("AxisPosition %1 failed").arg(list[i]));
			else
				m_axesPosSpins[i]->setValue(res);
		}
	}
}

void CTestForm::setTriggering()
{
	bool flag = m_ptTriggerChB->isChecked();
	if (!m_lib->setTriggering(flag))
		m_ptTriggerChB->setChecked(false);
}

void CTestForm::onSweepZBtn()
{
	if (!m_sweepZBtn->isChecked()) {
		if (!m_scanstopped && sweepZPars.sigsCnt == 0)
			m_lib->breakProbeSweepZ();
		return;
	}

	m_scanstopped = false;

	sweepZPars.pts = 20;
	sweepZPars.sigsCnt = 4;
	char sigs[4][MAX_SIG_NAME_LEN];
	strcpy(sigs[0], tr("Height(Sen)").toLatin1().data());
	strcpy(sigs[1], tr("Height(Dac)").toLatin1().data());
	strcpy(sigs[2], tr("Mag").toLatin1().data());
	strcpy(sigs[3], tr("Phase").toLatin1().data());
	float from = m_sweepFrom->value(), to = m_sweepTo->value();
	float sweepT = 10;
	float kIdleMove = 3;
	m_log->appendPlainText("Height(Sen), Height(Dac), Mag, Phase");

	m_lib->setScanCallback(::sweepZCallback);

	if (!m_lib->probeSweepZ(from, to, sweepZPars.pts, sweepT, kIdleMove, sweepZPars.sigsCnt, sigs)) {
		m_log->appendPlainText("Error. probeSweepZ failed.");
		m_sweepZBtn->setChecked(false);
	}
}

void CTestForm::emitSweepZCallback( int size, float * vals )
{
	if (m_scanstopped)
		return;
	paramLock();
	sweepZPars.vals.resize(size);
	for (int i = 0; i < size; i++)
		sweepZPars.vals[i] = vals[i];
	emit sigSweepZCallback();
	paramWaitUnlock();
}

void CTestForm::sweepZCallback()
{
	// Check user-stop; enable m_scanstopped flag before any other actions
	m_scanstopped = (!m_sweepZBtn->isChecked());

	// recieve sweepZ data
	int sz = sweepZPars.vals.size();
	if (sz){
		int npts = sz/sweepZPars.sigsCnt;
		//qDebug() << "npts" << npts << " sweepZPars.vals.size()" << sz << " sigsCnt" << sweepZPars.sigsCnt;
		QString stri = QString("Add sweepz pts %1").arg(npts);
		for ( int i = 0; i < sz; i++ )
			stri.append(QString("   %1").arg((int)sweepZPars.vals[i]));
		m_log->appendPlainText(stri);
		// If not user-stop, release the TScanCallback-function caller thread and return
		if (!m_scanstopped) {
			paramUnlock();
			return;
		}
	}
	else {
	// SweepZ was finished
		paramUnlock();
		m_sweepZBtn->setChecked(false);
		m_log->appendPlainText("Sweep Z finished\n");
		m_scanstopped = true;
		return;
	}
	// Was user-stop: obtained data size (sz) not zero; release the TScanCallback-function caller thread,
	// call BreakProbeSweepZ, then return
	if (m_scanstopped) {
		paramUnlock();
		m_lib->breakProbeSweepZ();
		m_log->appendPlainText("CTestForm::sweepZCallback SweepZ process was stopped by user.");
	}
}

void CTestForm::onLiftBtn()
{
	float lift = 100, triggerTime = 1;
	QString txt(tr("lift = %1 nm").arg(lift));
	if (m_ptTriggerChB->isChecked())
		txt += tr(", triggerTime = %1 sec").arg(triggerTime);
	m_log->appendPlainText(txt);
	if (m_lib->probeLift(lift, triggerTime))
		m_log->appendPlainText("ProbeLift finished.");
	else
		m_log->appendPlainText("Error: ProbeLift failed.");
}

void CTestForm::onLandBtn()
{
	if (m_lib->probeLand2())
		m_log->appendPlainText("ProbeLand finished.");
	else
		m_log->appendPlainText("Error: ProbeLand failed.");
}

void CTestForm::paramWaitUnlock()
{
	paramSemaphore.acquire();
	paramSemaphore.release();
}

void CTestForm::paramLock()
{
	paramSemaphore.acquire();
}

void CTestForm::paramUnlock()
{
	paramSemaphore.release();
}


int main ( int argc, char * argv[] )
{
    QApplication::setColorSpec( QApplication::CustomColor );
    QApplication a( argc, argv );

    CTestForm form;
    form.show();
    
    return a.exec();
}

