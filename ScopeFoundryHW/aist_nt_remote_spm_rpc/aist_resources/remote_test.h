#ifndef __REMOTE_TEST_H_
#define __REMOTE_TEST_H_

#include <QtGui>
class CRemoteCtrl;

class CTestForm: public QWidget
{
	Q_OBJECT
public:
	CTestForm( QWidget * p = 0 );
	~CTestForm();
	void emitLog( const QString & stri );
	void emitScanCallback( int size, float * vals );
	void emitCallback( int proc_index );
	void emitRestartLineCallback();
	void emitSweepZCallback( int size, float * vals );
protected slots:
	void init();
	void sendMessage();
	void checkCallback();
	void checkScanCallback();
	void axisRange();
	void signalsList();
	void onScanBtn();
	void onAxesPosBtn();
	void onAxesPosCb();
	void setTriggering();

	void slotLog( const QString & stri );

	void onSweepZBtn();
	void onLiftBtn();
	void onLandBtn();

signals:
	void sigLog( const QString & stri );
	void sigScanCallback();
	void sigCallback( int proc_index );
	void sigRestartLineCallback();
	void sigSweepZCallback();
private:
	bool m_initialized;
	QLineEdit * m_sendMsgEdit, * m_scnRngEdit;
	QPlainTextEdit * m_log;
	QPushButton * m_scanBtn;
	QComboBox * m_scanTypeCb, * m_planeIdCb;
	QCheckBox * m_ptTriggerChB;

	QPushButton * m_setAxesPosBtn;
	QList<QDoubleSpinBox *> m_axesPosSpins;
	QComboBox * m_axesPosCb;
	QDoubleSpinBox * m_axesPosTimeSb;

	QPushButton * m_sweepZBtn;
	QDoubleSpinBox * m_sweepFrom, * m_sweepTo;

	QPointer<CRemoteCtrl> m_lib;
	void mysleep(int tsleep);

	class CScanPars
	{
	public:
		float X0, Y0, W, H;
		float stepx, stepy;
		int line, linesCnt, linePts, sigsCnt;
		float tforw, tback;
		QVector<float> vals;
		bool procScanPoints;
		float tpoint;
		bool xyz, pass2;
		float tpass1, tpass2, tpass2back;
	};
	CScanPars scanPars;
	bool setupScanCommon();
	void procScanPoints();
	void execScanLine();
	
	void paramLock();
	void paramWaitUnlock();
	void paramUnlock();
	QSemaphore paramSemaphore;

	bool m_scanstopped;

	class CSweepZPars
	{
	public:
		int pts, sigsCnt;
		QVector<float> vals;
	};
	CSweepZPars sweepZPars;

private slots:
	void scanCallback();
	void callback( int proc_index );
	void restartLineCallback();
	void sweepZCallback();
};


#endif


