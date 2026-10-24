"""Vector A4 bench guide. Code is delivered as editable text, not PDF screenshots."""
from pathlib import Path
import json
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph,Table,TableStyle

NAVY=colors.HexColor('#123040');TEAL=colors.HexColor('#087c78');AMBER=colors.HexColor('#9b570e');RED=colors.HexColor('#a73442');INK=colors.HexColor('#243b46');GRAY=colors.HexColor('#617784');PALE=colors.HexColor('#edf5f7')
class Book:
    def __init__(self,path):
        self.c=canvas.Canvas(str(path),pagesize=A4,invariant=1);self.c.setTitle('PROMETHEUS - Final Staged Test Guide');self.c.setAuthor('Team Prometheus');self.n=0;self.y=0
    def page(self,title,subtitle=''):
        if self.n:self.c.showPage()
        self.n+=1;c=self.c;w,h=A4;c.setFillColor(NAVY);c.rect(0,h-42,w,42,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica-Bold',9);c.drawString(38,h-26,'TEAM PROMETHEUS  /  KITTY CORP');c.setFont('Helvetica',8);c.drawRightString(w-38,h-26,'STAGED BENCH TEST KIT - REV 1');c.setStrokeColor(colors.HexColor('#ccdade'));c.line(38,39,w-38,39);c.setFillColor(GRAY);c.setFont('Helvetica',8);c.drawString(38,25,'Wheels raised for all motor tests. A browser stop does not disconnect motor power.');c.drawRightString(w-38,25,str(self.n));self.y=h-76
        self.p(title,21,True,NAVY);self.p(subtitle,10,color=GRAY) if subtitle else None
    def p(self,text,size=10,bold=False,color=INK,gap=9):
        style=ParagraphStyle('body',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,leading=size*1.42,textColor=color)
        para=Paragraph(text,style);_,height=para.wrap(A4[0]-76,760);self.y-=height
        if self.y<55:raise ValueError(f'PDF page {self.n} overflow')
        para.drawOn(self.c,38,self.y);self.y-=gap
    def note(self,text,warning=False):self.p(('<b>HOLD / CHECK:</b> ' if warning else '<b>NOTE:</b> ')+text,10,color=RED if warning else TEAL)
    def steps(self,items):
        for i,item in enumerate(items,1):self.p(f'<b>{i}.</b> '+item)
    def table(self,head,rows,widths=None):
        width=A4[0]-76;widths=widths or [width/len(head)]*len(head)
        def cell(value,bold=False):return Paragraph(escape(str(value)),ParagraphStyle('cell',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=8.4,leading=11.3,textColor=colors.white if bold else INK))
        data=[[cell(v,True) for v in head]]+[[cell(v) for v in row] for row in rows]
        t=Table(data,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('ROWBACKGROUNDS',(0,1),(-1,-1),[PALE,colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,-1),.35,colors.HexColor('#c5d4da'))]));_,height=t.wrap(width,750);self.y-=height
        if self.y<55:raise ValueError(f'PDF table overflow page {self.n}')
        t.drawOn(self.c,38,self.y);self.y-=14
    def drawing(self,height,fn):
        self.y-=height
        if self.y<55:raise ValueError(f'PDF diagram overflow page {self.n}')
        self.c.saveState();self.c.translate(38,self.y);fn(self.c,A4[0]-76,height);self.c.restoreState();self.y-=15
    def save(self):self.c.save();return self.n

def label(c,x,y,text,size=9,color=INK,bold=False):
    c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.setFillColor(color);c.drawString(x,y,text)
def block(c,x,y,w,h,title,sub='',color=TEAL):
    c.setFillColor(PALE);c.setStrokeColor(color);c.setLineWidth(1.2);c.roundRect(x,y,w,h,6,fill=1,stroke=1);label(c,x+9,y+h-18,title,10,color,True)
    if sub:label(c,x+9,y+10,sub,8)
def wire(c,x1,y1,x2,y2,color=TEAL,dash=False):
    c.setStrokeColor(color);c.setLineWidth(1.6);c.setDash(5,3) if dash else c.setDash();c.line(x1,y1,x2,y2);c.setDash()
def chassis(c,w,h):
    block(c,70,12,w-140,h-25,'TEMPORARY BOX')
    label(c,70,0,'Placement diagram only; not a measured cutting template.',8,GRAY)
    block(c,w/2-62,h-53,124,27,'FRONT HC-SR04',color=TEAL)
    for x in (30,w-60):c.setFillColor(NAVY);c.roundRect(x,h-140,30,70,8,fill=1,stroke=0)
    block(c,70,h-130,72,46,'MOTOR A');block(c,w-142,h-130,72,46,'MOTOR B')
    wire(c,45,h-105,w-45,h-105,GRAY,True);label(c,170,h-95,'Align shaft centres',9,GRAY)
    block(c,155,h-155,90,32,'DRIVER');block(c,265,h-155,90,32,'ESP32')
    block(c,150,45,210,40,'DISCONNECTED HOLDERS','Low and secure inside support triangle')
    c.setFillColor(TEAL);c.circle(w/2,26,8,fill=1,stroke=0);label(c,w/2+20,23,'Rear caster',9)
def meter(c,w,h):
    block(c,12,35,146,90,'ISOLATED HOLDER',color=AMBER)
    label(c,25,87,'Robot disconnected',8,GRAY)
    label(c,25,65,'+ / output A',10,RED);label(c,25,48,'- / output B',10,INK)
    block(c,270,15,220,160,'MULTIMETER','DC VOLTAGE (V DC), not A or Ohm',NAVY)
    block(c,290,100,180,40,'Record sign + number','A reading is not a motor supply approval')
    for x,text,color in [(300,'COM',INK),(365,'V / VOhm',RED),(450,'10A',GRAY)]:
        c.setFillColor(color);c.circle(x,52,5,fill=1,stroke=0);label(c,x-17,33,text,8,color)
    wire(c,158,65,365,65,RED);wire(c,365,65,365,52,RED);wire(c,158,48,230,48,INK);wire(c,230,48,230,80,INK);wire(c,230,80,300,80,INK);wire(c,300,80,300,52,INK)
    wire(c,441,44,460,63,RED);wire(c,441,63,460,44,RED);label(c,14,140,'Red probe and black probe must not bridge the outputs.',9,RED)
def power(c,w,h):
    block(c,5,h-60,140,50,'USB INPUT','ESP32 Micro-USB',NAVY);block(c,190,h-60,125,50,'ESP32','3V3 logic + GND',TEAL);wire(c,145,h-35,190,h-35)
    block(c,w-150,h-60,145,50,'DRIVER LOGIC','VCC = reviewed 3.3 V',TEAL);wire(c,315,h-35,w-150,h-35);label(c,320,h-23,'3V3 -> VCC',8)
    wire(c,250,h-60,250,h-92,INK);wire(c,250,h-92,w-75,h-92,INK);wire(c,w-75,h-92,w-75,h-60,INK);label(c,255,h-83,'GND common reference',8,INK)
    block(c,5,35,130,60,'MOTOR SOURCE','Voltage/polarity unknown',AMBER);block(c,165,47,65,36,'FUSE',color=AMBER);block(c,260,47,86,36,'CUTOFF',color=AMBER);block(c,w-125,35,120,60,'DRIVER VM','IDENTIFY BEFORE USE',RED)
    wire(c,135,65,165,65,RED,True);wire(c,230,65,260,65,RED,True);wire(c,346,65,w-125,65,RED,True)
    wire(c,70,35,70,15,INK);wire(c,70,15,w-65,15,INK);wire(c,w-65,15,w-65,35,INK);label(c,160,2,'Direct motor return to source negative; common GND reference',8)
    label(c,170,105,'DASHED MOTOR POSITIVE = HOLD / DO NOT CONNECT YET',9,RED,True)
def driver(c,w,h,pins):
    block(c,5,30,155,h-45,'ESP32 GPIO LABELS','No physical header order is shown')
    block(c,250,30,125,h-45,'TB6612 LABELS','Actual VM / IC still pending')
    names=[(str(pins[key]),name) for key,name in [('Ain1','AIN1'),('Ain2','AIN2'),('Pwma','PWMA'),('Bin1','BIN1'),('Bin2','BIN2'),('Pwmb','PWMB'),('Standby','STBY')]]
    for i,(a,b) in enumerate(names):
        y=h-65-i*24;label(c,22,y,'GPIO'+a,9);label(c,268,y,b,9);wire(c,160,y+3,250,y+3,TEAL)
    block(c,405,h-95,103,52,'MOTOR A','AO1 + AO2',AMBER);block(c,405,55,103,52,'MOTOR B','BO1 + BO2',AMBER)
    wire(c,375,h-65,405,h-65,AMBER);wire(c,375,80,405,80,AMBER)
def divider(c,w,h,pins):
    label(c,0,h-18,'One verified 5 V-output sensor. Repeat the full divider for a rear sensor.',10,TEAL,True)
    y=h/2;label(c,0,y+7,'ECHO',9,RED,True);wire(c,45,y,85,y,RED);block(c,85,y-18,83,36,'2.2 kOhm',color=AMBER)
    wire(c,168,y,220,y,RED);c.setFillColor(TEAL);c.circle(220,y,3,fill=1,stroke=0);label(c,207,y-19,'J',10,TEAL,True)
    wire(c,220,y,260,y,TEAL);block(c,260,y-18,83,36,'2.2 kOhm',color=AMBER);wire(c,343,y,365,y,TEAL);block(c,365,y-18,72,36,'1 kOhm',color=AMBER);wire(c,437,y,493,y,INK);label(c,465,y-20,'GND',9)
    wire(c,220,y,220,y+47,TEAL);wire(c,220,y+47,382,y+47,TEAL);label(c,235,y+56,f'J -> GPIO{pins["FrontEcho"]} front / GPIO{pins["RearEcho"]} rear' ,9,TEAL)
    label(c,40,10,'Upper 2.2k; lower 2.2k + 1k in series = 3.2k. Nominal J = 2.963 V at 5 V.',9)
def indicators(c,w,h,pins):
    label(c,0,h-18,'LED (verified loose indicator)',10,TEAL,True);label(c,0,h-45,f'GPIO{pins["Led"]}' ,9);wire(c,48,h-42,88,h-42);block(c,88,h-60,90,36,'1 kOhm',color=AMBER);wire(c,178,h-42,225,h-42);label(c,230,h-46,'LED anode -> LED cathode -> GND',9)
    label(c,0,h-100,'Driver standby',10,TEAL,True);label(c,0,h-124,f'GPIO{pins["Standby"]}' ,9);wire(c,48,h-121,210,h-121);label(c,218,h-125,'STBY',9);wire(c,145,h-121,145,h-145);block(c,108,h-181,75,36,'10 kOhm',color=AMBER);wire(c,145,h-181,145,h-195,INK);label(c,165,h-197,'GND',9)
    label(c,0,31,f'Buzzer: GPIO{pins["Buzzer"]} -> VERIFIED compatible input/driver -> identified buzzer.' ,9,RED,True);label(c,0,13,'Do not connect an unknown buzzer load directly to a GPIO.',9,RED)

def create_pdf(path,plan,out):
    b=Book(path);pins=plan['pins'];width=A4[0]-76
    compile_path=Path(out)/'COMPILE-VERIFICATION.json';compile_info=json.loads(compile_path.read_text()) if compile_path.exists() else {}
    b.page('PROMETHEUS','Final staged testing guide | connections, joints, instruments, Arduino code and evidence')
    b.p('Build a real prototype, one verified test at a time.',17,True,TEAL)
    b.note('MOTOR POWER IS ON HOLD. Motor voltage/current, actual pack voltage/polarity and the driver VM/control labels are not confirmed by the supplied photos.',True)
    b.p('Photos show an ESP-32S-marked Micro-USB board, yellow TT-style motor/wheel and a red driver-style carrier. Successful ESP32 upload, Serial 115200, Wi-Fi scan, PROMETHEUS_ESP32 AP and the page at 192.168.4.1 are user-reported working. Do not restart those proofs unnecessarily.')
    b.table(['Delivered item','Purpose'],[['This PDF','Complete staged bench procedure and diagrams; hardware hold points remain active.'],['PROMETHEUS-CODE-CANVAS.html','Editable plain-text code tabs; no uploader and no device connection.'],['PrometheusTest folder','Complete Arduino IDE sketch and adjacent headers. Default: AP/Serial only; robot GPIOs uninitialized.'],['PROMETHEUS-ALL-CODE.txt','Text copy of every sketch/header. Split into the named files; not one giant sketch.'],['Verification JSON files','Checks actually run in the cloud; no claim of physical upload or motor tests.']],[160,width-160])
    b.p('This program is a commissioning tool: independent indicators, real sensor telemetry and deliberate, short raised-wheel motor pulses. It does not implement autonomous floor driving, path following or obstacle bypass.',11,True)
    status=compile_info.get('summary','Not yet verified in this draft; inspect COMPILE-VERIFICATION.json in the final package.')
    b.p('ESP32 compilation: '+escape(status),10,color=TEAL)
    b.p('Code stays in editable text files. No complete source listing is hidden in PDF images. Start with Test 01 on page 3; later stages require their own checks.')

    b.page('Readiness and stage order','A checked software setting is an operator declaration, not an electrical measurement.')
    b.table(['Evidence','Current status'],[['ESP32/AP/web page','User reports working; ESP-32S and Micro-USB visible.'],['Motor rating / stall current','Unknown; yellow plastic does not establish 3, 6 or 12 V.'],['Actual cells / pack output','Unknown. Earlier four-AA report is inventory context only.'],['Driver IC / VM / full pin bank','Not readable enough to release wiring. Do not use physical order or lead colour.'],['Fuse / cutoff / regulator','Not confirmed installed or rated.'],['Front / rear modules','Two HC-SR04s were reported; actual variants, power and interfaces need checking.'],['Printed body','V7.1 ordered by user; physical fitting not validated.']],[165,width-165])
    b.table(['Order','Run only this activity','Motor VM'],[['01','Isolated holder DC voltage/polarity','Disconnected'],['02','Unpowered joints, resistor values, pin identities and chassis','Disconnected'],['03','USB-only board and identified logic rails','Disconnected'],['04','Independent LED and sensor tests after interface review','Disconnected'],['05','Driver logic/STBY check','Disconnected'],['06','One-channel raised-wheel pulses, after power/load approval','Only after recorded review'],['07','Both-wheel, range guard, stop and communication checks','Raised wheels, cutoff reachable']],[40,355,width-395])
    b.note('If a prerequisite is unresolved, continue with an independent unpowered/logic activity. Do not invent a measured value to unlock code.')

    b.page('Test 01 / battery voltage','Parts: isolated holder/cells, multimeter. Code: none. Robot remains disconnected.')
    b.drawing(190,meter)
    b.steps(['Unplug ESP32 USB. Disconnect holder leads from the driver, breadboard and robot. Keep two holders separate; do not join them in series or parallel.',
      'Read and count the cells actually installed. If empty, report empty. Examples such as 6 V alkaline or 4.8 V NiMH are not identification of your pack.',
      'Black lead in COM. Red lead in the socket whose label includes V (a combined V/Ohm/mA socket can be correct). Do not use a separate 10A or current-only socket.',
      'Select DC volts (solid-over-dashed-line V symbol), not AC V, A/mA, Ohm or continuity. Use auto-range or start at the highest DC range. After a reading below 20 V, a 20 V range can improve resolution if available.',
      'Touch black to marked negative and red to marked positive; if unmarked, call outputs A/B and record probe locations. Do not bridge outputs with a probe tip.',
      'Record number, sign, unit and range. Negative means the red-probed output is lower potential than the black-probed output. Remove probes; leave holder disconnected.'])
    b.note('Never measure battery current by placing a meter across its outputs in A/mA mode. No spark or motor-stall test is requested.',True)
    b.p('<b>Result:</b> Holder A: ____ cells / label ____ / red on ____ / black on ____ / ____ V DC. Holder B separately: ____. A no-load reading does not prove load/current suitability.')

    b.page('Test 02 / chassis and joints','All USB and batteries disconnected. Parts: box, motors/wheels, caster, ties/brackets, insulating supports.')
    b.drawing(255,chassis)
    b.steps(['Align the two motor shaft centres on one transverse line. Wheels face outward, run parallel and clear the base. Secure motor bodies, not shafts.',
      'Fit rear caster height for three stable contacts without rocking. Keep holders low inside the support triangle, disconnected. Keep the phone off this first bare-base check.',
      'Mount electronics on insulating supports, retain USB/cutoff access, and route leads away from tyres and caster sweep. Use proper motor-current wires and connectors after current ratings are known.'])
    b.p('<b>Solder joints:</b> work only unpowered. Strip just enough wire for the terminal; tin the wire and lug, heat both together and let solder flow. Let it cool without moving, inspect for whiskers/bridges and gently tug-test. Insulate exposed joints. Do not overheat gearbox plastic or solder directly to cells. Hot glue is strain relief, not an electrical joint.')
    b.p('<b>Pass:</b> no rubbing/rocking or shifting motor bodies; secure insulated leads; readable labels. A photograph cannot certify that solder joints are short-free. A geared wheel need not free-spin; do not force it.')

    b.page('Unpowered meter checks','All sources removed, including USB. These checks do not prove load capability.')
    b.steps(['Move the red probe to the meter socket labelled V/Ohm and black to COM. Remove both USB and battery leads. Never select resistance or continuity on a powered circuit.',
      'Select continuity (sound-wave/diode symbol, using SELECT if required). Briefly touch the probe tips together to learn the normal beep/low-resistance response. Separate tips again.',
      'For a loose jumper, touch one probe to each end. A stable low resistance confirms that lead only. Wiggle gently to expose an intermittent connection. Label both ends with the terminal name.',
      'Trace one proposed connection at a time by printed terminal names. Probe the intended endpoints without bridging adjacent pins. Check whether breadboard power rails are split at the middle; do not assume the entire coloured rail is connected.',
      'Look for unintended adjacent-pin bridges, stranded-wire whiskers and reversed connectors. Remove detachable leads to isolate a suspicious connection. A rail capacitor can briefly beep while charging; persistent continuity is not by itself a diagnosis without the circuit context.',
      'Measure loose resistors in Ohm mode outside a parallel circuit, avoiding fingers across both leads. Read units carefully: 1k means 1000 Ohm; 2.2k means 2200 Ohm; 10k means 10000 Ohm. Verify tolerance/count for each divider and LED.',
      'Remove probes. Return the meter to DC volts and confirm the red lead is still in the V socket before a later powered rail check. Photograph/write the final endpoint list while everything remains disconnected.'])
    b.p('Do not use a continuity beep as proof that VCC/VM, a GPIO, motor winding or semiconductor circuit is correctly rated. Do not measure unknown motor stall current by holding the wheel or placing an ammeter across the battery. Obtain reliable motor/load data or suitable supervised current-limited characterization.')
    b.note('The current driver photos do not expose VM, the IC marking and every control label. Leave those lines unconnected until their actual functions are established.',True)

    b.page('Power distribution / HOLD','This is a net diagram by function, not a physical header-order drawing.')
    b.drawing(235,power)
    b.p('<b>ESP32:</b> use its supported Micro-USB input. Its regulator/3V3 pin is not a motor supply. <b>Driver VCC</b> is logic power; <b>VM</b> is motor power. Identify them separately on the real carrier.')
    b.p('<b>Common ground:</b> ESP32 GND, driver reference GND, sensor reference and motor-source negative share a reference. Motor return goes directly to its supply through suitable wiring, not through ESP32 headers or unsuitable breadboard rails. Do not parallel source positive rails.')
    b.note('Before VM: actual pack voltage/polarity and arrangement, motor operating voltage and startup/stall requirements, confirmed driver limits, rated fuse/cutoff/connectors and wire are required. A low PWM duty does not make an excessive supply voltage acceptable.',True)
    b.p('Fuse selection follows the real load, wire and interruption ratings. No fuse or regulator is assumed owned. The unknown 220 uF capacitor is not placed blindly: verify voltage rating, polarity, carrier decoupling and suitable location first.')
    b.p('A standard 5 V HC-SR04 needs an identified regulated 5 V distribution point. A board VIN/5V label is not automatically an approved output. Verify that carrier rail/function and budget first; do not use an ESP32 GPIO as power.')

    b.page('Driver / controller pin table','Candidate classic-ESP32 labels. Current physical wiring is not released.')
    b.table(['ESP32 label','TB6612 label','Function'],[[f'GPIO{pins[k]}',name,meaning] for k,name,meaning in [('Ain1','AIN1','Channel A direction 1'),('Ain2','AIN2','Channel A direction 2'),('Pwma','PWMA','Channel A PWM'),('Bin1','BIN1','Channel B direction 1'),('Bin2','BIN2','Channel B direction 2'),('Pwmb','PWMB','Channel B PWM'),('Standby','STBY','Disable low; check carrier enable/pull-up and proposed 10k pulldown')]], [105,100,width-205])
    b.table(['Driver terminal','Planned net'],[['AO1 / AO2','Two left-motor terminals (channel A)'],['BO1 / BO2','Two right-motor terminals (channel B)'],['VCC','Verified 3.3 V logic rail'],['GND terminal(s)','Verified common reference; proper direct motor return'],['VM','Protected, confirmed motor source positive: HOLD']],[125,width-125])
    b.p('A motor uses its two driver outputs; neither motor lead goes directly to ESP32/GND. A+ and B+ describe the electrical test direction until actual forward rotation and MotorASign/MotorBSign are observed. Never reverse battery polarity to correct a motor direction.')
    b.p('These candidates avoid classic ESP32 flash pins 6-11, straps 0/2/5/12/15 and UART0 1/3. Actual carrier conflicts still need inspection. Do not count physical pins from a board corner or copy a C3/S3 pinout.')

    b.page('Driver / logical connection diagram','Follow printed names. Wire colours in this figure do not identify your existing jumpers.')
    b.drawing(280,lambda c,w,h: driver(c,w,h,pins))
    b.steps(['With power removed, read and record every driver pin. VM and the main IC marking must be confirmed; fingers and wires obscure them in the supplied photos.',
      'Trace each wire end-to-end to the named destination. AO1/A01 printing can vary; clarify the legend rather than guessing from order.',
      'Inspect solder joints for bridges and whiskers. Later continuity checks are done only unpowered. A brief supply-rail beep can be capacitor charging; it alone does not diagnose a permanent short.'])
    b.note('Existing jumpers are not verified by their colour or by a successful ESP32 upload. The browser Assembly Lab uses a separate educational preset; this kit\'s pins.json / RobotPins.h is its candidate map.',True)

    b.page('Front and optional rear ultrasonic','Sensor power, pin identities and signal levels must be reviewed first. Motors stay off for independent tests.')
    b.table(['Net','Front candidate','Rear candidate (optional)'],[['TRIG',f'GPIO{pins["FrontTrig"]}',f'GPIO{pins["RearTrig"]}'],['Conditioned ECHO',f'GPIO{pins["FrontEcho"]}',f'GPIO{pins["RearEcho"]}'],['VCC','Verified supply for actual variant','Same requirement'],['GND','Common reference','Common reference']],[120,195,width-315])
    b.drawing(175,lambda c,w,h: divider(c,w,h,pins))
    b.p(f'GPIO{pins["RearTrig"]}/{pins["RearEcho"]} rear candidates require actual availability and no PSRAM/carrier conflict. Rear remains disabled until checked. Triggering is staggered with quiet intervals; no physical cross-talk result is claimed.')
    b.p('For the 5 V-output example, lower resistance is 3.2k in series, not parallel. Nominal J is 2.963 V. Under assumed 4.75-5.25 V input and independent +/-5% resistors, calculated J is 2.699-3.237 V. Compare actual supply, drive, resistors and identified GPIO limits/thresholds before acceptance. A 3.3 V-output variant may need a different interface.')
    b.table(['Resistors to verify/count','Front + LED','Both sensors + LED'],[['2.2 kOhm','2','4'],['1 kOhm','2','3'],['10 kOhm STBY pulldown','1, carrier review needed','1, carrier review needed']],[230,130,width-360])
    b.note('No raw 5 V ECHO to a GPIO. No-echo/invalid/stale is not clear space. This PDF\'s 2.2k-upper divider supersedes the older unapproved 2k-upper example for this test kit.',True)

    b.page('LED, standby and buzzer','Unknown buzzer remains disconnected; an output pin is not a power driver.')
    b.drawing(265,lambda c,w,h: indicators(c,w,h,pins))
    b.p('LED: use a verified loose low-current indicator and a separate 1k series resistor. Confirm anode/cathode; clipped lead length is not reliable. Resistor orientation is not polarized.')
    b.p('Standby: verify a compatible carrier and any STBY pull-up/jumper before adopting the 10k pulldown. It should hold the driver disabled during reset; a steady meter reading alone does not characterize very short boot glitches. Initial motor power tests use raised wheels and reachable cutoff.')
    b.p('Buzzer: identify active/passive type, rated voltage/current, signal polarity and input circuit. Some modules expose 5 V on their input; some loads need a transistor driver. BuzzerMode supports ActiveHigh, ActiveLow or Passive2kHz only after a compatible interface is verified. Do not select a mode by pin count alone.')
    b.table(['State','Simple indication if its hardware is enabled'],[['Waiting / connected','Slow LED blink; motor setup can still be locked'],['Motor test pulse','LED steady'],['Obstacle / fault / stop latch','Fast LED plus intermittent buzzer'],['Pulse complete','Two brief LED flashes / brief buzzer chirp']],[165,width-165])

    b.page('Arduino IDE / code files','Use the existing working IDE setup. Do not paste every file into one sketch.')
    b.steps(['Extract the ZIP. Open PrometheusTest/PrometheusTest.ino. Keep Dashboard.h, HttpGate.h, RobotPins.h, SafetyCore.h and Settings.h beside it. Arduino IDE should show them as tabs.',
      'Select ESP32 Dev Module for the reported classic ESP32. Select the port that belongs to this connected board; COM8 was observed previously, not guaranteed permanently. Serial Monitor: 115200 baud, Newline.',
      'First use Verify/Compile. Keep the distributed Settings.h values unchanged for the USB/AP-only profile. Disconnect all robot jumpers and motor power before any board-only upload.',
      'Uploading replaces the earlier demo sketch. The AP name remains PROMETHEUS_ESP32; this sketch generates/stores its own password and prints it to Serial. Do not assume the old saved Wi-Fi password still matches.',
      'Join that AP on phone/laptop and open http://192.168.4.1/. No internet is needed. Default LOCKED with N/A sensors is expected; it does not mean upload failed.',
      'Use PROMETHEUS-CODE-CANVAS.html for text editing/copying. Save changed files into the matching sketch folder. It is not a direct Arduino uploader; edits are not automatically saved.'])
    b.p('The code has Arduino ESP32 2.x/3.x LEDC compatibility branches and targets classic ESP32 only. Actual compile results/versions are recorded in COMPILE-VERIFICATION.json. No source has been uploaded to your board by this cloud task.')
    b.note('Do not set verification flags merely to clear LOCKED. The program cannot inspect fuse ratings, motor specifications, raised wheels or physical wiring.',True)

    b.page('Stage settings / deliberate unlock','Keep all unrelated flags false. Values come from actual checks, not this table.')
    b.table(['Code flag in Settings.h','Meaning'],[['BoardPinLabelsVerified','The actual board GPIO/supply labels and conflicts were checked.'],['DriverLabelsLogicAndStandbyVerified','Driver identity, every terminal, logic supply and standby circuit checked.'],['MotorSupplyRatingsCurrentFuseAndWiringVerified','Motor/driver current and voltage, pack, polarity, protection and wiring reviewed.'],['WheelsRaisedAndBaseSecured','The physical base is restrained with wheels clear of any surface.'],['AllowNoRangeRaisedWheelTest','Explicit exception only for the motor-only raised-wheel stage.'],['FrontSensorPowerAndEchoVerified / RearSensorPowerEchoAndPinsVerified','Actual sensor power/level interface and candidate pins checked.'],['LedResistorAndPolarityVerified','Low-current LED, series resistor and polarity checked.'],['BuzzerInterfaceVerified + BuzzerMode','Identified compatible buzzer input/driver, supply and active/passive behavior.']],[245,width-245])
    b.p('MeasuredMotorPackV, VerifiedMotorSupplyMinV and VerifiedMotorSupplyMaxV start at zero and keep motor tests locked. Enter the actual measured pack voltage and a reliably established acceptable supply interval only after the power/load review. No interval is inferred from motor appearance.')
    b.table(['Profile','Enable only after its physical checks'],[['USB/AP','No robot verification flags; zero voltage fields'],['LED','Board + LED'],['Front sonar','Board + front sensor'],['Both sonar modules',f'Board + front + rear, including GPIO{pins["RearTrig"]}/{pins["RearEcho"]} check' ],['Driver logic, VM off','Board + driver logic/standby'],['Motor-only bench','Board + driver + motor electrical + raised wheels + explicit no-range bench exception + valid real voltage fields'],['Guarded motor bench','Board + driver + motor electrical + raised wheels + front (and verified rear if used); no-range exception off']],[135,width-135])

    b.page('Independent logic tests','Run only after that stage\'s interface has been checked. Motor source remains disconnected.')
    b.table(['Test','Parts / connection','Code / command','Expected observation'],[['LED',f'GPIO{pins["Led"]} -> 1k -> LED anode; cathode -> GND' ,'Verified Board+LED profile; Serial led or web LED','Solid LED for 1.5 s, then normal status pattern'],['Front range',f'Front sensor and its full verified divider; GPIO{pins["FrontTrig"]}/{pins["FrontEcho"]}' ,'Board+Front profile; status / telemetry','Actual distances change with a broad flat target; invalid/no echo shows N/A'],['Rear range',f'Separate verified module/divider; GPIO{pins["RearTrig"]}/{pins["RearEcho"]} available' ,'Board+Front+Rear profile','Independent front/rear readings; check for cross-talk'],['Driver standby','Verified VCC/GND and signal labels; VM disconnected','Board+Driver profile; remain LOCKED','Check steady STBY near GND and stable logic rail; no motor action'],['Buzzer',f'Identified compatible input/driver; GPIO{pins["Buzzer"]} reserved' ,'Board+Buzzer profile and correct mode; beep','150 ms expected sound; no motor output']],[70,170,135,width-375])
    b.p('Measure isolated resistors in Ohm mode only with power removed. Switch the meter back to DC volts before powered rail checks. Do not probe adjacent header pins with wide exposed tips or perform continuity checks on a powered board.')
    b.p('For range tests, compare against a ruler at several known distances with a broad flat target. Include near/blocked, no-echo and disconnected-sensor cases. Soft, angled, narrow objects and floor reflections can be missed. Standard no-echo is an invalid result, not an assumed 4 m distance.')
    b.note('Front data alone does not measure side, rear, table edges or the robot\'s swept turn clearance. Keep this kit on its raised-wheel support.',True)

    b.page('Raised-wheel motor test','BLOCKED until the electrical review and physical setup are complete.')
    b.steps(['Record actual supply and motor/driver/protection compatibility. Confirm VM terminal and polarity. Set up a reachable hardware cutoff; secure the chassis and lift both tyres clear of the surface. Clear loose leads from wheels.',
      'With power removed, connect channel A to its two motor terminals and B to its two terminals; connect reviewed logic/control/ground nets. Check all endpoints, solder joints and protection before applying the reviewed source.',
      'Choose only the reviewed motor profile. Default test duty is 48/255 and pulse is 150 ms; neither is proof of suitable voltage, current or slow physical movement. Do not increase duty to overcome an unknown electrical fault.',
      'Serial command test a+ runs one A-only pulse. Then inspect the result. Repeat test a- only after the first observation is acceptable. Next use test b+ and test b-. Other channel output should remain zero.',
      'If direction is opposite, disconnect motor power before changing wiring or MotorASign/MotorBSign. If left/right is swapped, correct MotorALeft or the reviewed channel wiring. Never reverse supply polarity.',
      'After individual channels pass, deliberately test forward, back, left and right with wheels still raised. Each command is one short pulse, then COMPLETE with zero outputs. No automatic repeating while holding a button.'])
    b.p('<b>Stop immediately:</b> unexpected movement at boot, persistent movement after a pulse, reset/brownout, unstable logic/range, heating, an unsecured wire or wheel, or failed cutoff. Do not continue to a floor route to diagnose it.')
    b.p('<b>Pass evidence:</b> record channel, observed direction, actual supply, duty, pulse duration and stop result. COMPLETE means elapsed test timing, not a measured distance or verified motor speed.')

    b.page('Stops, obstacles and watchdog','Software behavior must be observed on the actual setup; cloud tests do not establish stopping time.')
    b.table(['Test','Method / expected result'],[['Range before arm','With an object within 200 mm, arm must fail. Require three fresh samples at/above 300 mm after clearing before a new arm.'],['Active range stop','With helper/recording and raised wheels, move a broad target into range during a deliberate pulse. OBSTACLE, zero outputs and STBY disable must be observed. COMPLETE from timer expiry alone does not prove the range stop.'],['Sensor missing / stale','With motor power off, arrange the reviewed fault test. On an enabled sensor becoming invalid/stale during an armed test, expect FAULT and zero outputs. Never simulate the fault by shorting a pin or applying 5 V to a GPIO.'],['Stop latch','Use web LATCH STOP / Space or Serial stop. Expect ESTOP; ordinary Disarm does not clear it. Reset then a new explicit arm is required.'],['Command lease','Arm without a pulse, then stop owner heartbeats/disconnect its Wi-Fi. Expect command-lease FAULT after the 400 ms limit, subject to actual scheduling. A late heartbeat must not revive it.'],['Pulse hard limit','The normal 150 ms pulse usually finishes before the 400 ms lease. Seeing COMPLETE at 150 ms is not proof of watchdog expiry.'],['Reboot / tab leave','Power/reset and page blur/hiding must not restart motion. Rejoining Wi-Fi or reopening a page alone never arms.']],[120,width-120])
    b.p('The local control task checks independently of HTTP. Sensor reads are bounded in a separate task. A nominal 10 ms control period is not a certified latency guarantee; record observed reaction and motor coast/brake behavior. The physical cutoff is independent of the browser and firmware.')

    b.page('Dashboard and API','The ESP32 hosts this page. Opening dashboard.html from disk is not a device connection.')
    b.p('Connect phone/laptop to PROMETHEUS_ESP32 using the password printed by this sketch, then browse to http://192.168.4.1/. Default indicators/sensors/motor controls reflect enabled stages, not a remote electrical inspection. N/A stays N/A; battery voltage/current and travel are not measured by this code.')
    b.table(['Interface','Contract'],[['GET /','Lightweight local dashboard; no CDN/login/internet dependency'],['GET /api/state','Actual mode/reason, signed PWM, remaining ms, valid range or null, configuration enables, session token, sequence and sample ID'],['POST /api/command','Form fields action, client (24 hex), seq (increasing uint32), and duty 1..80 for motion; X-Prometheus-Token header; same-origin robot page'],['Actions','arm, heartbeat, stop, estop, reset, a+, a-, b+, b-, forward, back, left, right, led, beep'],['Ownership','The active controlling client owns motion/heartbeats. Other clients can request stop. New starts require deliberate arm.'],['Limits','One configured pulse, 50..250 ms hard bound; distributed default 150 ms. Overlapping pulses cannot extend it. Command lease 400 ms; range freshness 250 ms.'],['Rejections','Malformed/stale/unauthorized or wrong-owner commands reject. HTTP errors are not evidence of a physical action.']],[135,width-135])
    b.p('Serial Monitor with Newline: help, status, stop, reset, led, beep, test a+, test a-, test b+, test b-, test forward, test back, test left, test right. A Serial test combines a deliberate arm and one pulse; it never automatically clears a fault/stop latch.')
    b.p('Request admission caps headers at 1536 bytes, the form body at 256 bytes and the complete request at 2048 bytes. Four input slots expire incomplete requests after 350 ms. This is not a guaranteed network stop latency; the local pulse limit and hardware cutoff remain independent.')
    b.p('Polling alone does not keep a pulse alive. The dashboard renews the controlling lease while explicitly armed; blur/hide sends a best-effort stop and drops renewals. Device-local expiry/hard limit still governs if that packet is lost.')

    b.page('Common mistakes / diagnosis','Disconnect motor power before correcting any wiring.')
    b.table(['Symptom / mistake','Check / correction'],[['LOCKED or disabled motor buttons','Expected with supplied settings. Complete real checks; do not flip flags or invent voltage values just to unlock.'],['Upload connects but fails','Use the already working board/port/data cable. Disconnect peripherals. Close Serial Monitor for upload; inspect the actual error before driver/core changes.'],['New AP password rejected','This sketch stores/prints its own password. Read Serial; forget an old saved network profile if necessary.'],['Missing Dashboard.h / RobotPins.h','Extract and open the full PrometheusTest folder with all headers beside .ino.'],['ledcSetup / ledcAttach errors','Use the included version-compatible source. Do not copy only part of it; compare core version with compile report.'],['Board resets when a motor starts','Use cutoff. Recheck supply sag, startup current, return routing, decoupling and solder joints; not simply a Wi-Fi bug.'],['Motor does not move','Cut power before tracing VM/VCC/STBY, driver pin labels, output pairs, secure joints and core reason. PWM may be below starting torque; do not blindly raise voltage/duty.'],['One wheel direction wrong','Check channel/polarity at raised wheels; adjust reviewed motor sign/channel mapping with power removed.'],['N/A ultrasonic','Check actual variant/supply, common reference, trigger, divider node, echo timeout and target geometry. Never bypass divider to try raw 5 V.'],['Meter near zero / OL','Confirm voltage mode, correct jacks, range and probe contact. Do not switch to current mode across a battery.'],['App looks ready, wiring unknown','Configuration is an operator declaration. Software cannot inspect motor ratings, fuses, solder or physical clearance.']],[165,width-165])

    b.page('Record and decide the next stage','Do not mark a physical test passed from a compile or browser fixture.')
    b.table(['Record','Actual observation'],[['Motor / supplier voltage and stall/start requirements','________________________________________'],['Driver IC, VM/VCC, all signal/output labels','________________________________________'],['Holder cells / chemistry / arrangement','________________________________________'],['DMM voltage, polarity, probes/range','________________________________________'],['Fuse, switch, wire/connector ratings','________________________________________'],['Logic rails / ECHO interface / resistor values','________________________________________'],['A+/A- and B+/B- directions, duty and supply','________________________________________'],['Boot/reset, pulse expiry, ESTOP and cutoff','________________________________________'],['Front/rear range accuracy, invalid/stale response','________________________________________'],['Owner-link loss and explicit rearm behavior','________________________________________'],['Actual reaction time / stopping observation','________________________________________'],['Unresolved issues / next permitted activity','________________________________________']],[250,width-250])
    b.p('Next integration: only after these checks, develop calibrated timed floor movement and a drawn route with a distinct estimated trace. Without encoders/position feedback there is no precise localization. One fixed forward sensor cannot choose a safe side; rotating the robot to scan still needs independently cleared swept space. Unknown recovery should end BLOCKED / REPLAN REQUIRED, not a silent claim that the original route was regained.')
    b.p('Autonomous bypass, path drawing/execution, camera AI and precise navigation are not implemented in this bench-test sketch. The existing bench_motion source is a separate prototype; the printable V7.1 fit also remains a separate physical check. This guide does not grant motor-power approval while the documented measurements are missing.',10,True,RED)
    return b.save()
