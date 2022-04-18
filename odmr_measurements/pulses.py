# pulses.py
# Copyright 2018 Diana Prado Lopes Aude Craik

# Permission is hereby granted, free of charge, to any person 
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

def makeCPMGpulses(start_delay, numberOfPiPulses, t_delay, t_pi, t_piby2, IQpadding):
    t_piby4 = t_piby2 / 2;
    if numberOfPiPulses == 1:
        uWstartTimes = [start_delay, start_delay + t_delay - t_piby4, start_delay + 2 * t_delay] 
        uWdurations = [t_piby2, t_pi, t_piby2]
    else:
        half_t_delay = t_delay / 2
        # Start off the sequence by adding the initial pi/2 and first pi pulse
        uWstartTimes = [start_delay, start_delay + half_t_delay - t_piby4] 
        uWdurations = [t_piby2, t_pi]
        # Add remaining pi pulses:
        for i in range(1, numberOfPiPulses):
            currentEdgeTime = uWstartTimes[-1] + t_delay
            uWstartTimes.append(currentEdgeTime)
            uWdurations.append(t_pi)
        # Append the final pi/2 pulse:
        uWstartTimes.append(uWstartTimes[-1] + half_t_delay + t_piby4)
        uWdurations.append(t_piby2)
    # Make the I and Q channel pulses:
    # Q is ON during pi(y) pulses and the final pi/2(-x), but not the first pi/2(x) pulse
    QstartTimes = [x - IQpadding for x in uWstartTimes[1:]]
    Qdurations = [x + 2 * IQpadding for x in uWdurations[1:]]
    # I is only on during the final pi/2(-x) pulse:
    IstartTimes = [x - IQpadding for x in [uWstartTimes[-1]]]
    Idurations = [x + 2 * IQpadding for x in [uWdurations[-1]]]
    return [uWstartTimes, uWdurations, IstartTimes, Idurations, QstartTimes, Qdurations]

    
def makeXY8pulses(start_delay, numberOfRepeats, t_delay, t_pi, t_piby2, IQpadding):
    t_piby4 = t_piby2 / 2
    # Start off the sequence by adding the initial pi/2:
    half_t_delay = t_delay / 2
    uWstartTimes = [start_delay] 
    uWdurations = [t_piby2]
    QstartTimes = []
    Qdurations = []
    # Add remaining pi pulses:
    firstPiPulseDone = False
    for i in range(0, numberOfRepeats):
        # Make next 8 pi pulses:
        next8piPulseStartTimes = []
        next8piPulseDurations = []
        # Add the first pulse in the set of 8
        currentEdgeTime = 0
        if not firstPiPulseDone:
            currentEdgeTime = uWstartTimes[-1] + half_t_delay - t_piby4
            firstPiPulseDone = True
        else:
            currentEdgeTime = uWstartTimes[-1] + t_delay
        next8piPulseStartTimes.append(currentEdgeTime)
        next8piPulseDurations.append(t_pi)
        for j in range (1, 8):
            newEdgeTime = next8piPulseStartTimes[-1] + t_delay
            next8piPulseStartTimes.append(newEdgeTime)
            next8piPulseDurations.append(t_pi)
        # Make next 8 Q start times (Q is only on for pulses 1,3,4,6 of the xy8 pi pulses, for a 0-indexed sequence):
        next8QstartTimes = list(next8piPulseStartTimes[i] for i in [1, 3, 4, 6])
        next8Qdurations = list(next8piPulseDurations[i] for i in [1, 3, 4, 6])
        # Append next 8 pi pulses and Q pulses to start times lists:
        uWstartTimes.extend(next8piPulseStartTimes)
        uWdurations.extend(next8piPulseDurations)
        QstartTimes.extend(next8QstartTimes)
        Qdurations.extend(next8Qdurations)
        
    # Append the final pi/2 pulse:
    uWstartTimes.append(uWstartTimes[-1] + half_t_delay + t_piby4)
    uWdurations.append(t_piby2)
    # Append the final pi/2 pulse to Q channel since (in the signal bin) Q is on for this pulse as it is a -x pulse.
    QstartTimes.append(uWstartTimes[-1])
    Qdurations.append(uWdurations[-1])
    # Pad the Q channel pulses:
    QstartTimes = [x - IQpadding for x in QstartTimes]
    Qdurations = [x + 2 * IQpadding for x in Qdurations]
    # Make I channel pulses. I is only on during the final pi/2(-x) pulse:
    IstartTimes = [x - IQpadding for x in [uWstartTimes[-1]]]
    Idurations = [x + 2 * IQpadding for x in [uWdurations[-1]]]
    return [uWstartTimes, uWdurations, IstartTimes, Idurations, QstartTimes, Qdurations]
    