"""Host tests for the actual backlight/command functions; not a hardware build."""
from pathlib import Path
import subprocess, tempfile
source = (Path(__file__).resolve().parents[1] / 'Firmware_BLE.ino').read_text()
def function(name):
    start = source.index('void ' + name + '(')
    opening = source.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]
assert 'SCREEN_ON_MS' not in source
assert 'actualizarAhorroPantalla' not in source
assert '31.5f*0.8f,33.5f*0.8f' in source
assert '31.0f*0.8f,33.0f*0.8f' in source
code = r'''
#include <cassert>
#include <cstring>
#include <string>
#include <cstdint>
const int HIGH=1,LOW=0,LCD_BL=46;
int pin=-1, writes=0;
bool screenBacklightOn=true;
void digitalWrite(int p,int value){assert(p==LCD_BL);pin=value;++writes;}
unsigned millis(){return 1234;}
'''+function('iniciarAhorroPantalla')+r'''
struct Harness {
 struct Command {unsigned epoch;char text[32];};
 unsigned activeEpoch=9,streamHz=20,lastS=0;
 bool v2=true,needHello=false,needState=false,needOx=false,needPrv=false,needDiag=false;
 std::string reply;
 void response(const char* s){reply=s;}
'''+function('handleCommand')+r'''
 void send(const char* s,unsigned epoch=9){Command c{};c.epoch=epoch;strcpy(c.text,s);reply.clear();handleCommand(c);}
};
int main(){
 iniciarAhorroPantalla();assert(pin==HIGH);
 Harness h;
 h.send("SCREEN:GET");assert(h.reply=="ACK:SCREEN:ON" && writes==1);
 h.send("SCREEN:OFF");assert(pin==LOW && h.reply=="ACK:SCREEN:OFF");
 h.send("SCREEN:OFF");assert(pin==LOW); // idempotent retry
 h.send("SCREEN:GET");assert(h.reply=="ACK:SCREEN:OFF");
 h.send("SCREEN:ON",8);assert(pin==LOW && h.reply.empty()); // stale epoch
 h.activeEpoch=10;h.send("SCREEN:GET",10);assert(h.reply=="ACK:SCREEN:OFF"); // reconnect
 h.send("SCREEN:ON",10);assert(pin==HIGH && h.reply=="ACK:SCREEN:ON");
 h.v2=false;h.send("SCREEN:OFF",10);assert(pin==HIGH && h.reply=="ERR:HELLO_REQUIRED");
 h.v2=true;h.send("SCREEN:INVALID",10);assert(pin==HIGH && h.reply=="ERR:UNKNOWN");
 h.send("STREAM:0",10);assert(h.streamHz==0 && h.reply=="ACK:STREAM:0");
 h.send("STREAM:20",10);assert(h.streamHz==20 && h.reply=="ACK:STREAM:20");
 h.send("GET:STATE",10);assert(h.needState && h.reply=="ACK:GET:STATE");
 h.send("SCREEN:OFF",10);iniciarAhorroPantalla();assert(pin==HIGH);
}
'''
with tempfile.TemporaryDirectory() as tmp:
    cpp=Path(tmp)/'screen.cpp';cpp.write_text(code)
    executable=Path(tmp)/'screen'
    subprocess.run(['g++','-std=c++17','-Wall','-Wextra','-Werror',str(cpp),'-o',str(executable)],check=True)
    subprocess.run([str(executable)],check=True)
print('PASS: actual command handler, boot, OFF/ON/GET, retries, epoch, reconnect and legacy commands')
