require( "qt.ice" )

if RemoteQnami then
	RemoteQnami:delete()
end

local CRemoteCtrl = class( CWidget )

function CRemoteCtrl:__init()
	self[ CWidget ]:__init()
	self:setParentMain()
	self:setWindowTitle('Remote ctrl')

	local vlt = CreateLayout(2, 6, 0)
	self:setLayout(vlt)
	vlt:setSizeConstraint(3)

	local t = CPushButton()
	self.initBtn = t
	t:setText("Enable")
	t:setToolTip( "This button enables and disables external control mode." )
	t:setFixedSize(75, 30)
	t:setCheckable(true)
	vlt:addWidget(t)
	t:connect("click", self, self.onInitClick)

	-- self:connect( "close", self, self.onClose )
	self:show()
	
	-- self.scanTimer = CTimer()
	-- self.scanTimer:setInterval(200)
	-- self.scanTimer:connect("timeout", self, self.onScanTimer)

end


function CRemoteCtrl:delete()
	-- √лобальна€ внешн€€ переменна€ дл€ вызова.
	RemoteQnami = nil
	
	if self.Scan then
		self.Scan:delete()
	end

	if self.TestCallbackTimer then
		if self.testCallbackInd then
			self.testCallbackInd = nil
			self.TestCallbackTimer:stop()
		end
		self.TestCallbackTimer:delete()
	end
	
	if self.TestScanCallbackTimer then
		if self.testScanCallbackInd then
			self.testScanCallbackInd = nil
			self.TestScanCallbackTimer:stop()
		end
		self.TestScanCallbackTimer:delete()
	end

	Dw_Message("CRemoteCtrl:delete()")
	if self.c then
		self.c:destroy()
		while ( self.c:isConnected() ) do
		end
		self.c:delete()
	end	
	if self.s then
		self.s:destroy()
		while( self.s:isConnected() ) do
		end
		self.s:delete()
	end
	self[ CWidget ]:delete()
end


function CRemoteCtrl:onInitClick()
	if self.initBtn:isChecked() then
		local s = CIceServer()
		s:setAdapter("ba-ba-ba", "myTestAdapter", "default -p 54321")
		s:setProperty("Ice.ACM.Client", "0")
		s:start()
		while ( s:isConnecting() ) do
		end
		assert( s:isConnected() )

		self.s = s
		
		local c = CIceClient()
		c:setServer("myTestAdapter:default -p 54321")
		c:setProperty("Ice.ACM.Client", "0")
		c:start()
		while ( c:isConnecting() ) do
		end
		assert( c:isConnected() )
		self.c = c

		c:connect("SendLogMessage",			self, self.sendLogMessage)
		c:connect("InitTestCallback",		self, self.initTestCallback)
		c:connect("InitTestScanCallback",	self, self.initTestScanCallback)
		c:connect("AxisRange",				self, self.axisRange)
		c:connect("AxisPosition",			self, self.axisPosition)
		c:connect("SetAxisPosition",		self, self.setAxisPosition)
		c:connect("SetAxesPositions",		self, self.setAxesPositions)
		c:connect("AxisSetpoint",			self, self.axisSetpoint)
		c:connect("SignalsList",			self, self.signalsList)
		c:connect("SetupScanCommon",		self, self.setupScanCommon)
		c:connect("SetupScanLine",			self, self.setupScanLine)
		c:connect("ExecScanPoint",			self, self.execScanPoint)
		c:connect("FinitScan",				self, self.finitScan)
		c:connect("ExecScanLine",			self, self.execScanLine)
		c:connect("EnablePtTrigger",		self, self.enablePtTrigger)
		
		Dw_MessageU('Remote contol is enabled.')
	else
		if self.c then
			self.c:destroy()
			while ( self.c:isConnected() ) do
			end
			self.c:delete()
		end
		if self.s then
			self.s:destroy()
			while ( self.s:isConnected() ) do
			end
			self.s:delete()
		end
		self.s = nil
		self.c = nil
		Dw_MessageU('Remote contol is disabled.')
	end
end



function CRemoteCtrl:sendLogMessage( msg )
	Dw_MessageU(msg)
	self.c:callSlotAll("answer", string.format("The message \"%s\" has been received", msg))
end

function CRemoteCtrl:initTestCallback()
	if not self.TestCallbackTimer then
		self.TestCallbackTimer = CTimer()
		self.TestCallbackTimer:setInterval(2000)
		self.TestCallbackTimer:connect("timeout", self, self.onTestCallbackTimer)
	end
	self.testCallbackInd = 1
	self.TestCallbackTimer:start()
end

function CRemoteCtrl:onTestCallbackTimer()
	if not self.testCallbackInd then
		return
	end
	self.c:callSlotAll("callback", self.testCallbackInd)
	self.testCallbackInd = self.testCallbackInd + 1
	if self.testCallbackInd > 5 then
		self.testCallbackInd = nil
		self.TestCallbackTimer:stop()
	end
end

function CRemoteCtrl:initTestScanCallback()
	if not self.TestScanCallbackTimer then
		self.TestScanCallbackTimer = CTimer()
		self.TestScanCallbackTimer:setInterval(1000)
		self.TestScanCallbackTimer:connect("timeout", self, self.onTestScanCallbackTimer)
	end
	self.testScanCallbackInd = 1
	self.TestScanCallbackTimer:start()
end

function CRemoteCtrl:onTestScanCallbackTimer()
	if not self.testScanCallbackInd then
		return
	end
	local res = {}
	for i = 1, self.testScanCallbackInd do
		res[i] = (i-1.)/self.testScanCallbackInd
	end
	self.c:callSlotAll("scanCallback", unpack(res))
	self.testScanCallbackInd = self.testScanCallbackInd + 1
	if self.testScanCallbackInd > 7 then
		self.testScanCallbackInd = nil
		self.TestScanCallbackTimer:stop()
	end
end


local Signals = {}

Signals.Names = { 'Height(Dac)', 'Height(Sen)', 'Iprobe', 'Mag', 'Phase', 'Freq', 
				'Nf', 'Lf',  'Ex1', 'SenX', 'SenY', 'SenZ', 'SenX2', 'SenY2', 'SenZ2' }
Signals.Inds = { ["Height(Dac)"] = 100, ["Height(Sen)"] = 2, Iprobe = 12, Mag = 21, Phase = 24, Freq = 127,
				Nf = 13, Lf = 14, Ex1 = 15, SenX = 0, SenY = 1, SenZ = 2, SenX2 = 32, SenY2 = 33, SenZ2 = 34 }

local c = -131072
Signals.Biases = { ["Height(Dac)"] = 0, ["Height(Sen)"] = 0, Iprobe = c, Mag = 0, Phase = c, Freq = -200000, 
				Nf = c, Lf = c, Ex1 = c, SenX = 0, SenY = 0, SenZ = 0, SenX2 = 0, SenY2 = 0, SenZ2 = 0  }
Signals.Scales = {}
Signals.Units = {}
for i, name in ipairs(Signals.Names) do
	Signals.Scales[name] = 1
	Signals.Units[name] = 'a.u.'
end
Signals.Scales.Sum = -1
Signals.Scales.Phase = 1.3733e-3
Signals.Units.Phase = 'deg'
Signals.Units["Height(Sen)"] = 'nm'
Signals.Units["Height(Dac)"] = 'nm'
Signals.Units.Iprobe = "pA"

function Signals:update()
	local scale, bias, units

	-- Height(Sen)
	bias = -afm10.ctrl.getSignal(2)
	scale = afm10.getValue('Scn1/SEN/calibr/3') * 0.1
	self.Biases["Height(Sen)"] = bias
	self.Scales["Height(Sen)"] = scale

	-- Height(Dac)
	bias = -afm10.ctrl.getSignal(100)
	scale = afm10.getValue('Scn1/HV/calibr/3') * 0.1 * afm10.getValue("hv10/0/hv_z_scale")/65535
	self.Biases["Height(Dac)"] = bias
	self.Scales["Height(Dac)"] = scale

	-- freq
	scale = ( afm10.getValue("dfm/FreqX10") > 0 ) and 0.1 or 0.01
	self.Scales.Freq = scale

	-- IProbe
	if CurrentSwitch then
		self.Scales.Iprobe = CurrentSwitch.IprC
	end

	-- scale, units = probeCalibrs:magScale()
	-- self.Scales.Mag = scale
	-- self.Units.Mag = units
end

local printTable = 
function( Tab, pattern, title )
	local str = title or ''
	for i = 1, #Tab do
		str = string.format('%s' .. pattern, str, Tab[i])
	end
	Dw_Message(str)
end

-- extra = error string or table or nil
function CRemoteCtrl:answer( res, extra )
	if not res then
		if extra then
			Dw_MessageU(extra)
		end
		self.c:callSlotAll("answer", false)--, extra)
	else
		if type(res) == 'table' then
			self.c:callSlotAll("answer", unpack(res))
		else
			if extra then
				self.c:callSlotAll("answer", res, unpack(extra))
			else
				self.c:callSlotAll("answer", res)
			end
		end
	end
end

-- scnInd = 1..2, axInd = 1,2,3 (X, Y, Z); sigInd = 0, 1, 2, 32, 33, 34; fbInd = 1, 2, 0, 4, 5, 3
local getAxisInds = 
function( axisId )
	axisId = tostring(axisId):lower()
	local scnInd, axInd, sigInd, fbInd
	if axisId == 'x' or axisId == 'x1' then 
		scnInd, axInd, sigInd, fbInd = 1, 1, 0, 1
	elseif axisId == 'y' or axisId == 'y1' then
		scnInd, axInd, sigInd, fbInd = 1, 2, 1, 2
	elseif axisId == 'z' or axisId == 'z1' then
		scnInd, axInd, sigInd, fbInd = 1, 3, 2, 0
	elseif axisId == 'x2' then
		scnInd, axInd, sigInd, fbInd = 2, 1, 32, 4
	elseif axisId == 'y2' then
		scnInd, axInd, sigInd, fbInd = 2, 2, 33, 5
	elseif axisId == 'z2' then
		scnInd, axInd, sigInd, fbInd = 2, 3, 34, 3
	end
	return scnInd, axInd, sigInd, fbInd
end

local calibrations = 
function( scnInd, axInd )
	local id = string.format('Scn%i/SEN/calibr/%i', scnInd, axInd)
	local scale = afm10.getValue(id)/10000.
	-- For 1st scanner Z axis
	if scnInd == 1 and scale < 0 then
		id = string.format('Scn%i/SEN/bound2/%i', scnInd, axInd)
	else
		id = string.format('Scn%i/SEN/bound1/%i', scnInd, axInd)
	end
	local b1 = afm10.getValue(id)
	if scnInd == 2 then
		scale = math.abs(scale)
	end
	return scale, b1, afm10.scannerCfg[scnInd]:maxRange(axInd, 'SEN')
end

local enableFeedback = 
function(fbInd, sigInd)
	if afm10.getValue("fbEnabled" .. fbInd) <= 0 then
		local sen = afm10.ctrl.getSignal(sigInd)
		if sen then
			afm10.setValue('fbSetpoint' .. fbInd, sen)
		end
		afm10.fbCtrl.enable(fbInd, 1, true)
	end
end

-- axisId: X, Y, Z (X1, Y1, Z1); X2, Y2, Z2; output: um
function CRemoteCtrl:axisRange( axisId )
	if not afm10.devOpened then
		return self:answer(0)
	end
	local scnInd, axInd = getAxisInds(axisId)
	local res = 0
	if scnInd and afm10.scannerCfg[scnInd] then
		res = afm10.scannerCfg[scnInd]:maxRange(axInd, 'SEN')
	end
	Dw_Message('axisRange %s, res = %.2f', axisId, res)
	self:answer(res)
	return res
end

function CRemoteCtrl:axisPosition( axisId )
	if not afm10.devOpened then
		Dw_MessageU('Device is closed. AxisPosition failed')
		return self:answer(-1000)
	end
	local scnInd, axInd, sigInd = getAxisInds(axisId)
	if (not scnInd) or (not afm10.scannerCfg[scnInd]) then
		Dw_MessageU('Wrong axisId: %s. AxisPosition failed', tostring(axisId))
		return self:answer(-1000)
	end
	-- local rng = afm10.scannerCfg[scnInd]:maxRange(axInd, 'SEN')
	local sen = afm10.stateCtrl.getAverSignals(sigInd, sigInd, 5)
	local scale, b1 = calibrations(scnInd, axInd)
	local res = ( sen - b1 ) * scale
	Dw_Message('axisPosition %s = %.2f, scale = %.3f, b1 = %i', axisId, res, 10000*scale, b1)
	self:answer(res)
end

function CRemoteCtrl:setAxisPosition( axisId, value, sweepTime )
	if not afm10.devOpened then
		return self:answer(false, 'Device is closed. SetAxisPosition failed')
	end
	local scnInd, axInd, sigInd, fbInd = getAxisInds(axisId)
	if (not scnInd) or (not afm10.scannerCfg[scnInd]) then
		return self:answer(false, 'Wrong axisId: ' .. tostring(axisId) .. '. SetAxisPosition failed')
	end

	if fbInd == 0 then
		local zfbname = afm10.fbCtrl.ZFbNames[afm10.getValue('fbInIndex0') + 1]
		if zfbname ~= 'SenZ' then
			return self:answer(false, 'Error! Z-feedback input signal must be "SenZ"')
		end
	end
	enableFeedback(fbInd, sigInd)

	local scale, b1, rng = calibrations(scnInd, axInd)
	if value < 0 then value = 0
	elseif value > rng then value = rng end
	local sen = value/scale + b1
	afm10.fbCtrl.setpoint(fbInd, sen, 1000 * sweepTime)
	if sweepTime > 0.05 then
		sen = afm10.stateCtrl.getAverSignals(sigInd, sigInd, 5)
		value = (sen - b1)*scale
	end
	self.c:callSlotAll("answer", true, value)
end

function CRemoteCtrl:setAxesPositions(sweepTime, ...)
	sweepTime = tonumber(sweepTime) or 1
	if sweepTime < 0.001 then sweepTime = 0.001 end
	if not afm10.devOpened then
		return self:answer(false, 'Device is closed. SetAxesPositions failed')
	end
	local tt = {...}
	local axesCnt = math.floor(#tt/2.)
	if 2*axesCnt ~= #tt or axesCnt < 1 then
		return self:answer(false, 'Wrong arguments list. SetAxesPositions failed')
	end
	local axesIds, values = {}, {}
	for i = 1, axesCnt do
		table.insert(axesIds, tostring(tt[i]))
	end
	for i = axesCnt + 1, 2*axesCnt do
		table.insert(values, tonumber(tt[i]) or 0)
	end
	
	local Axes, Targs, SigInds, B1s, Scales = {}, {}, {}, {}, {}
	local scnInd, axInd, sigInd, fbInd
	local scale, b1, rng, value, sen
	
	for i = 1, axesCnt do
		scnInd, axInd, sigInd, fbInd = getAxisInds(axesIds[i])
		
		if (not scnInd) or (not afm10.scannerCfg[scnInd]) then
			return self:answer(false, 'Wrong axisId: ' .. tostring(axesIds[i]) .. '. SetAxesPositions failed')
		end

		if fbInd == 0 then
			local zfbname = afm10.fbCtrl.ZFbNames[afm10.getValue('fbInIndex0') + 1]
			if zfbname ~= 'SenZ' then
				return self:answer(false, 'Error! Z-feedback input signal must be "SenZ"')
			end
		end
		
		enableFeedback(fbInd, sigInd)
		
		scale, b1, rng = calibrations(scnInd, axInd)
		value = values[i]
		if value < 0 then value = 0
		elseif value > rng then value = rng end
		values[i] = value
		sen = value/scale + b1
		
		table.insert(Axes, fbInd)
		table.insert(Targs, sen)
		table.insert(SigInds, sigInd)
		table.insert(B1s, b1)
		table.insert(Scales, scale)
	end
	
	afm10.fbCtrl.sweepAxes2(Axes, Targs, sweepTime)
	if sweepTime > 0.1 then
		for i = 1, axesCnt do
			sen = afm10.stateCtrl.getAverSignals(SigInds[i], SigInds[i], 5)
			values[i] = (sen - B1s[i])*Scales[i]
		end
	end
	self:answer(true, values)

end

function CRemoteCtrl:axisSetpoint( axisId )
	if not afm10.devOpened then
		Dw_MessageU('Device is closed. AxisSetpoint failed')
		return self:answer(-1000)
	end
	local scnInd, axInd, sigInd, fbInd = getAxisInds(axisId)
	if (not scnInd) or (not afm10.scannerCfg[scnInd]) then
		Dw_MessageU('Wrong axisId: %s. AxisSetpoint failed', tostring(axisId))
		return self:answer(-1000)
	end
	
	if fbInd == 0 then
		local zfbname = afm10.fbCtrl.ZFbNames[afm10.getValue('fbInIndex0') + 1]
		if zfbname ~= 'SenZ' then
			Dw_MessageU('Error! Z-feedback input signal must be "SenZ"')
			return self:answer(-1000)
		end
	end

	local sp = afm10.getValue('fbSetpoint'..fbInd)
	local scale, b1 = calibrations(scnInd, axInd)
	local res = ( sp - b1 ) * scale
	Dw_Message('axisSetpoint %s = %.2f, scale = %.3f, b1 = %i', axisId, res, 10000*scale, b1)
	self:answer(res)
end

function CRemoteCtrl:signalsList()
	local tab = {}
	for i, name in ipairs(Signals.Names) do
		table.insert(tab, name)
		table.insert(tab, Signals.Units[name])
	end
	self:answer(tab)
	return tab
end


local CScan = class()

function CScan:__init( owner )
	self.owner = owner
end

function CScan:delete()
	Dw_Message('CScan:delete')
	if self.timer then
		self.timer:delete()
	end
end

function CScan:init( scnInd, axInd0, axInd1, linePts, scanMode )
	if afm10.slotsHV10cnt < scnInd then
		Dw_MessageU('Error! No scanner-board to control scanner%i', scnInd)
		return false
	end
	self.scnInd = scnInd 
	local inSigs = {0, 1, 2, 32, 33, 34}
	local fbInds = {1, 2, 0, 4, 5, 3}
	self.inSig0 = inSigs[axInd0 + 3*(scnInd - 1)]
	self.inSig1 = inSigs[axInd1 + 3*(scnInd - 1)]
	self.fbInd0 = fbInds[axInd0 + 3*(scnInd - 1)]
	self.fbInd1 = fbInds[axInd1 + 3*(scnInd - 1)]
	self.linePts = linePts
	self.pointScanMode = (scanMode ~= 0)
	Dw_MessageU('Scan mode: %s', self.pointScanMode and 'point-scan' or 'line-scan')

	self.calibrs = {}
	self.calibrs.scaleX, self.calibrs.bx1 = calibrations(scnInd, axInd0)
	self.calibrs.scaleY, self.calibrs.by1 = calibrations(scnInd, axInd1)
	
	self.firstPtFlag = true
	self.line = nil -- см. CRemoteCtrl:execScanLine или execScanPoint
	self.ScanMsrFuncId = aist3Spec and aist3Spec.ScanMsrFuncId or 12
	self.ptTriggerFlag = false
	return self:initClosedLoop()
end

function CScan:setSignalsList( sigs )
	self.sigNames = {}
	for i, name in ipairs(sigs) do
		if not Signals.Inds[name] then
			return false
		end
		table.insert(self.sigNames, name)
	end
	self.sigInds, self.sigScales, self.sigBiases = {}, {}, {}

	Signals:update()
	for i, name in ipairs(self.sigNames) do
		table.insert(self.sigInds, Signals.Inds[name])
		table.insert(self.sigScales, Signals.Scales[name])
		table.insert(self.sigBiases, Signals.Biases[name])
	end
	return true
end

--[[function CScan:calibrations()
	return self.calibrs.scaleX, self.calibrs.scaleY, self.calibrs.bx1, self.calibrs.by1
end]]

function CScan:senFromCoor( x, axInd )
	if axInd == 2 then
		return x/self.calibrs.scaleY + self.calibrs.by1
	else
		return x/self.calibrs.scaleX + self.calibrs.bx1
	end
end

function CScan:coorFromSen( x, axInd )
	if axInd == 2 then
		return ( x - self.calibrs.by1 )*self.calibrs.scaleY
	else
		return ( x - self.calibrs.bx1 )*self.calibrs.scaleX
	end
end

function CScan:setupScanLine( x0, y0, x1, y1, tforw, tback )
	self.line = {}
	local l = self.line
	x0, y0 = self:senFromCoor(x0, 1), self:senFromCoor(y0, 2)
	x1, y1 = self:senFromCoor(x1, 1), self:senFromCoor(y1, 2)
	l.xstep, l.ystep = (x1 - x0)/(self.linePts - 1), (y1 - y0)/(self.linePts - 1)
	l.x0, l.y0 = x0, y0 -- for execScanPoint

	if self.pointScanMode then
		l.xmsr1, l.ymsr1 = x0, y0
		l.xbeg, l.ybeg = x0, y0
	else
		l.xmsr1, l.ymsr1 = x0 - 0.5 * l.xstep, y0 - 0.5 * l.ystep
		local overscan = 0.03 
		if 1./(self.linePts - 1.) < overscan then
			l.xbeg = x0 - (x1 - x0) * overscan
			l.ybeg = y0 - (y1 - y0) * overscan
		else
			l.xbeg = x0 - l.xstep
			l.ybeg = y0 - l.ystep
		end
	end
	
	l.tforw, l.tback = tforw, tback
	-- ѕо умолчанию, при ненулевых размерах пол€, tforw определ€ет скорость на пр€мом ходу, tback на обратном
	-- ≈сли размеры пол€ нулевые, пусть скорость будет диапазон за 5 секунд = 140000/5
	-- ѕауза на развороте (point/line-scan mode) при ненулевом размере пол€ = pointT;
	-- при нулевом поле пауза = 0, если нет перемещени€. »наче пусть будет 100 ms.
	-- ƒл€ line-scan mode интервалов на 1 больше, поэтому pointT = tforw/linePts - корректно, в случае сканировани€
	-- в точке тоже подходит
	-- ƒл€ point-scan mode (ненулевое поле) pointT = tforw/(linePts-1)
	-- ƒл€ нулевого размера пол€ в point-scan mode пусть присылают tforw = 0
	l.pointT = self.pointScanMode and l.tforw/(self.linePts-1) or l.tforw/self.linePts
	l.ptIndex = 0

end

function CScan:scannerPos( flag_um )
	local x, y = afm10.stateCtrl.getAverSignals(self.inSig0, self.inSig1, 10)
--[[	if not ( x and y ) then
		Dw_MessageU("ERROR reading x, y position")
		return
	end]]
	if not flag_um then
		return x, y
	else
		return coorFromSen(x, 1), coorFromSen(y, 2)
	end
end

function CScan:updateFbSetpoints()
	local x, y = self:scannerPos()
	if not (x and y) then return end
	Dw_Message('CScan:updateFbSetpoints %i %i', x, y)
	afm10.setValue('fbSetpoint' .. self.fbInd0, x)
	afm10.setValue('fbSetpoint' .. self.fbInd1, y)
end

function CScan:initClosedLoop()

	if self.fbInd0 == 0 or self.fbInd1 == 0 then
		local zfbname = afm10.fbCtrl.ZFbNames[afm10.getValue('fbInIndex0') + 1]
		if zfbname ~= 'SenZ' then
			Dw_MessageU('Error! Z-feedback input signal must be "SenZ"')
			return false
		end
	end

	local x, y
	if (afm10.getValue("fbEnabled" .. self.fbInd0) == 0) then
		x, y = self:scannerPos()
		if x then
			afm10.setValue('fbSetpoint' .. self.fbInd0, x)
		end
		afm10.fbCtrl.enable(self.fbInd0, 1)
	end
	if (afm10.getValue("fbEnabled" .. self.fbInd1) == 0) then
		if not y then
			x, y = self:scannerPos()
		end
		if y then
			afm10.setValue('fbSetpoint' .. self.fbInd1, y)
		end
		afm10.fbCtrl.enable(self.fbInd1, 1)
	end
	return true
end

-- T[s], if T == nil выполн€етс€ один раз
function CScan:waitForFinish( T )
	local t = T and os.time()
	repeat
		ReadSPM()
		local v = vReadData(5, 0)
		if v then
			Dw_Message('waitForFinish ' .. v)
			res = true
			break
		end
		if T then
			Delay(10)
		else
			break
		end
	until ( os.time() - t > T )
	return res
end

-- if not Twait[s] and no data, return nil
-- Not readSPM for Twait = nil
function CScan:measurePt( Twait )

	local cnt = #self.sigInds
	if cnt <= 0 then
		return {}
	end

	-- специально не делаем ReadSPM
	if GetDataCnt(self.ScanMsrFuncId, cnt-1) == 0 then
		if Twait then
			local t = os.time()
			local res = false
			while ( os.time() - t < Twait ) do
				ReadSPM()
				if GetDataCnt(self.ScanMsrFuncId, cnt-1) > 0 then
					res = true
					break
				end
				Delay(10)
			end
			if not res then
				return
			end
		end
	end

	local vals = {}
	for k = 1, cnt do
		local val = vReadData(self.ScanMsrFuncId, k-1)
		if not val then
			Dw_Message( "no data. dataId = " .. k-1 )
			val = -1000
		else
			val = ( val + self.sigBiases[k] ) * self.sigScales[k]
		end
		table.insert(vals, val)
	end

	return vals
end

-- tpoint [sec]; need for point-scan only
function CScan:execScanLine( tpoint )
	if self.pointScanMode then
		Dw_Message('execScanLine tpoint = %.2f sec', tpoint)
	end
	if self.firstPtFlag then
		self:initLineProc()
		self.firstPtFlag = false
	end
	local l = self.line
	local x1, y1, x2, y2, pauseT, backT, ptT, msr1stT, stayPtT

	x1, y1 = l.xbeg, l.ybeg
	local nsteps = self.pointScanMode and self.linePts - 1 or self.linePts
	x2, y2 = l.xmsr1 + l.xstep * nsteps, l.ymsr1 + l.ystep * nsteps
	
	local x, y = self:scannerPos()
	local line_sz = (l.xstep * l.xstep + l.ystep * l.ystep) * nsteps * nsteps
	line_sz = math.sqrt(line_sz)
	local dist = math.sqrt((x - x1) * (x - x1) + (y - y1) * (y - y1))
--[[		Dw_Message('line_sz %i  dist %i  linePts %i  xstep %i  ystep %i  tback %i',
							line_sz, dist, self.linePts, l.xstep, l.ystep, l.tback)]]
	if line_sz > 0 then
		backT = l.tback/line_sz * dist
		pauseT = l.pointT
	else
		backT = dist/140000 * 5 -- 5 sec на полный диапазон сканера
		pauseT = (dist > 0) and 0.1 or 0
	end
	
	ptT = l.pointT

	if line_sz > 0 then
		dist = math.sqrt((l.xmsr1 - x1) * (l.xmsr1 - x1) + (l.ymsr1 - y1) * (l.ymsr1 - y1))
		msr1stT = dist/line_sz * l.tforw
	else
		msr1stT = 0
	end
	
	-- Ќенулевой backT и msr1stT + ptT * ptsCnt
	if backT == 0 then
		backT = 1/500000.
	end
	if msr1stT == 0 and ptT == 0 then
		msr1stT = 1/500000.
	end

	stayPtT = tpoint

	Dw_Message('execScanLine x1 %i  xmsr1 %i  y1 %i  x2 %i  y2 %i\npauseT %ims  backT %ims' .. 
	'  ptT %ims  msr1stT %ims  linePts %i',
			x1, l.xmsr1, y1, x2, y2, 1000*pauseT, 1000*backT, 1000*ptT, 1000*msr1stT, self.linePts)

	local CASE_NEXT_LINE = 1
	SetUserVar(1, x1)
	SetUserVar(2, y1)
	SetUserVar(3, x2)
	SetUserVar(5, y2)
	SetUserVar(6, 500000*pauseT)
	SetUserVar(7, 500000*backT)
	SetUserVar(8, 500000*ptT)
	if self.pointScanMode then
		SetUserVar(9, 500000*stayPtT)
	else
		SetUserVar(9, 500000*msr1stT)
	end
	SetUserVar(10, self.linePts)
	-- чтобы User0 всегда был от x1 до x2
	local kPulseInd = math.floor((x2 - x1)/(self.linePts+1) + 0.5)
	SetUserVar(12, kPulseInd)
	SetUserVar(0, CASE_NEXT_LINE)
	
	if not self.timer then
		self.timer = CTimer()
		self.timer:setInterval(200)
		self.timer:setSingleShot(true)
		self.timer:connect("timeout", self, self.onTimer)
	end
	self.timer:start()
	self.readPtsCnt = 0
	return true
end

function CScan:onTimer()
	-- Dw_Message('CScan:onTimer')
	if not self.line then return end
	local vals = {}
	local cnt = #self.sigInds
	local stop_flag = false
	if cnt > 0 then
		local ptsCnt = GetDataCnt(self.ScanMsrFuncId, cnt-1)
		for pt = 1, ptsCnt do
			for k = 1, cnt do
				local val = vReadData(self.ScanMsrFuncId, k-1)
				if not val then
					Dw_Message("no data. dataId = %, pt = %i", k-1, pt)
					val = -1000
				else
					val = ( val + self.sigBiases[k] ) * self.sigScales[k]
				end
				table.insert(vals, val)
			end
		end
		self.readPtsCnt = self.readPtsCnt + #vals
		stop_flag = (self.readPtsCnt == self.linePts * cnt)
		if #vals > 0 then
			self.owner.c:callSlotAll("scanCallback", unpack(vals))
			-- printTable(vals, '%i ')
			if self.owner.testScanCallback then
				self.owner.testScanCallback(vals)
			end
		end
	else
		stop_flag = self:waitForFinish()
	end
	if not stop_flag then
		self.timer:start()
	else
		Dw_MessageU('Scan line finished')
		self.owner.c:callSlotAll("scanCallback")
		if self.owner.testScanCallback then
			self.owner.testScanCallback()
		end
	end
end

function CScan:execScanPoint()
	if self.firstPtFlag then
		self:initPointProc()
		self.firstPtFlag = false
	end
	local l = self.line
	local CASE_NEXT_PT = 1
	if l.ptIndex == self.linePts then
		Dw_Message('execScanPoint: last line pt data')
		SetUserVar(0, 10) -- not CASE_NEXT_PT
		local vals = self:measurePt(2)
		local res
		if not vals then
			self.owner:answer(false, 'execScanPoint ' .. l.ptIndex .. 'failed')
		else
			self.owner:answer(true, vals)
			printTable(vals, '%i ', 'pt_last ')
			res = true
		end
		l.ptIndex = 0 -- зачем?
		-- self:updateFbSetpoints()
		return res
	end

	local x1, y1, T, pauseT
	x1 = l.x0 + l.ptIndex * l.xstep
	y1 = l.y0 + l.ptIndex * l.ystep
	if l.ptIndex == 0 then
		local x, y = self:scannerPos()
		local line_sz = (l.xstep * l.xstep + l.ystep * l.ystep) * (self.linePts-1) * (self.linePts-1)
		line_sz = math.sqrt(line_sz)
		local dist = math.sqrt((x - l.x0) * (x - l.x0) + (y - l.y0) * (y - l.y0))
--[[		Dw_Message('line_sz %i  dist %i  linePts %i  xstep %i  ystep %i  tback %i',
							line_sz, dist, self.linePts, l.xstep, l.ystep, l.tback)]]
		if line_sz > 0 then
			T = l.tback/line_sz * dist
			pauseT = l.pointT
		else
			T = dist/140000 * 5 -- 5 sec на полный диапазон сканера
			pauseT = (dist > 0) and 0.1 or 0
		end
	else
		T = l.pointT
		pauseT = 0
	end
	Dw_Message('execScanPoint %i, %i  T = %i ms  pauseT = %i ms', x1, y1, 1000*T, 1000*pauseT)
	T, pauseT = 500000 * T, 500000 * pauseT
	if T < 1 then T = 1 end
	SetUserVar(1, x1)
	SetUserVar(2, y1)
	SetUserVar(3, T)
	SetUserVar(5, pauseT)
	afm10.stateCtrl.clearing(0)
	SetUserVar(0, CASE_NEXT_PT)
	local res
	if self:waitForFinish(0.000002*(T + pauseT) + 2) then
		if l.ptIndex == 0 then
			self.owner:answer(true)
			res = true
			Dw_Message('pt0 okay')
		else
			local vals = self:measurePt()
			if not vals then
				self.owner:answer(false, 'execScanPoint ' .. l.ptIndex .. 'failed')
			else
				self.owner:answer(true, vals)
				res = true
				printTable(vals, '%i ', string.format('pt%i ', l.ptIndex))
			end
		end
		l.ptIndex = l.ptIndex + 1
	else
		self.owner:answer(false, 'execScanPoint ' .. l.ptIndex .. 'failed')
		res = false
	end
	return res
end

function CScan:initPointProc()
	Dw_Message("CScan:initPointProc()")

	SetParam(1002, 0)
	SetUserVar(0, self.fbInd0)
	SetUserVar(1, self.fbInd1)

	afm10.stateCtrl.clearing(0, 10) -- for Send(0, 12345)
	
	local sigsCnt = #self.sigInds
	Dw_Message("Sigs cnt: " .. sigsCnt)
	if (sigsCnt == 0) then
		SetUserVar(4, 0)
		afm10.scanCtrlFb.enableAver(false)
	else
		afm10.scanCtrlFb.setupScanMsr(self.sigInds, self.ScanMsrFuncId)
		afm10.scanCtrlFb.clearScanMsr(sigsCnt, self.ScanMsrFuncId)
		SetUserVar(4, sigsCnt)
		afm10.scanCtrlFb.enableAver(true)
	end

	LoadMacro("macros/qnami/point_mover.dsp")
	SetParam(1002, 1)
end

function CScan:initLineProc()
	Dw_Message("CScan:initLineProc")

	SetParam(1002, 0)
	SetUserVar(0, self.fbInd0)
	SetUserVar(1, self.fbInd1)
	local flagPulses = self.ptTriggerFlag and 1 or 0
	SetUserVar(2, flagPulses)

	afm10.stateCtrl.clearing(0, 10) -- for Send(0, 12345)
	
	local sigsCnt = #self.sigInds
	Dw_Message("Sigs cnt: " .. sigsCnt)
	if (sigsCnt == 0) then
		SetUserVar(4, 0)
		afm10.scanCtrlFb.enableAver(false)
	else
		afm10.scanCtrlFb.setupScanMsr(self.sigInds, self.ScanMsrFuncId)
		afm10.scanCtrlFb.clearScanMsr(sigsCnt, self.ScanMsrFuncId)
		SetUserVar(4, sigsCnt)
		afm10.scanCtrlFb.enableAver(true)
	end

	if self.pointScanMode then
		LoadMacro("macros/qnami/linepts_mover.dsp")
	else
		LoadMacro("macros/qnami/line_mover.dsp")
	end
	SetParam(1002, 1)
end

function CScan:finitScan()
	Dw_MessageU('CScan:finitScan')
	if self.line then
		SetParam(1002, 0)
		self.line = nil
		if self.timer then
			self.timer:stop()
		end
		self:updateFbSetpoints()
	end
end

function CRemoteCtrl:setupScanCommon( planeId, linePts, scanMode, ... )
	if not afm10.devOpened then
		return self:answer(false, 'setupScanCommon: SPM is not initialized')
	end

	planeId = tostring(planeId):lower()
	local scnInd, axInd0, axInd1
	if planeId == 'xy' or planeId == 'x1y1' then
		scnInd = 1
		axInd0, axInd1 = 1, 2
	elseif planeId == 'xz' or planeId == 'x1z1' then
		scnInd = 1
		axInd0, axInd1 = 1, 3
	elseif planeId == 'yz' or planeId == 'y1z1' then
		scnInd = 1
		axInd0, axInd1 = 2, 3
	elseif planeId == 'x2y2' then
		scnInd = 2
		axInd0, axInd1 = 1, 2
	elseif planeId == 'x2z2' then
		scnInd = 2
		axInd0, axInd1 = 1, 3
	elseif planeId == 'y2z2' then
		scnInd = 2
		axInd0, axInd1 = 2, 3
	end

	linePts = tonumber(linePts)
	linePts = linePts and math.floor(linePts)

	scanMode = tonumber(scanMode)
	scanMode = scanMode and math.floor(scanMode)

	if (not scnInd) or (not linePts) or (linePts < 2) or (not scanMode) then
		self:answer(false, 'setupScanCommon: wrong planeId or linePts or scanMode')
		return
	end

	self.Scan = self.Scan or CScan(self)
	if not self.Scan:init(scnInd, axInd0, axInd1, linePts, scanMode) then
		self:answer(false)
		return
	end
	local sigs = {...}
	if not self.Scan:setSignalsList(sigs) then
		self:answer(false, 'setupScanCommon: wrong sigs list')
		return
	end
	self:answer(true)
	return true
end

function CRemoteCtrl:enablePtTrigger()
	Dw_Message('CRemoteCtrl:enablePtTrigger')
	if self.Scan then
		self.Scan.ptTriggerFlag = true
	end
end

function CRemoteCtrl:finitScan()
	if self.Scan then
		self.Scan:finitScan()
	end
	-- No answer
	-- self:answer(true)
end

function CRemoteCtrl:setupTrigger( at_pt_begin, line )
end

function CRemoteCtrl:setupScanLine( x0, y0, x1, y1, tforw, tback )
	if not self.Scan then
		self:answer(false, 'setupScanLine: Scan common setup was not performed')
		return
	end
	x0, y0, x1, y1 = tonumber(x0), tonumber(y0), tonumber(x1), tonumber(y1)
	tforw, tback = tonumber(tforw), tonumber(tback)
	if not (x0 and y0 and x1 and y1 and tforw and tback) then
		self:answer(false, 'setupScanLine: wrong or not enough input parameters')
		return
	end
--[[	if (x0 == x1 and y0 == y1) then
		return self:answer(false, 'setupScanLine: x0 == x1 and y0 == y1')
	end]]
	if (tforw <= 0 or tback <= 0) then
		self:answer(false, 'setupScanLine: tforw <= 0 or tback <= 0')
		return
	end
	Dw_Message('setupScanLine x0y0x1y1  %.1f  %.1f  %.1f  %.1f  tforw = %.1f  tback = %.1f',
					x0, y0, x1, y1, tforw, tback)
	self.Scan:setupScanLine(x0, y0, x1, y1, tforw, tback)
	self:answer(true)
	return true
end

function CRemoteCtrl:execScanLine( tpoint )
	if (not self.Scan) or (not self.Scan.line) then
		self:answer(false, 'execScanLine: Scan setup was not completed')
		return
	end
	local res = self.Scan:execScanLine(tpoint)
	self:answer(res)
	return res
end

function CRemoteCtrl:execScanPoint()
	if (not self.Scan) or (not self.Scan.line) then
		self:answer(false, 'execScanPoint: Scan setup was not completed')
		return
	end
	return self.Scan:execScanPoint()
end

function CRemoteCtrl:moveCallback( scnInd )
	self.c:callSlotAll("callback", scnInd)
end

addMacroProc("externalNotify", tii_externalNotify)

RemoteQnami = CRemoteCtrl()
