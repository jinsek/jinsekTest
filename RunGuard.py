#coding=utf-8
import os
import sys
import shutil
import math
import subprocess
import time
import threading
import ctypes
import ConfigParser

#command code 1 --- exit guard, 2 ---- killexit
g_CmdCode = 0
g_mutex = threading.Lock()

def kill(pid):
    """kill function for Win32"""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(1, 0, pid)
    return (0 != kernel32.TerminateProcess(handle, 0))

def InputThreadMain():
    global g_CmdCode, g_mutex
    #线程名
    threadname = threading.currentThread().getName()
    g_mutex.acquire()
    print threadname, ' started. \n'
    g_mutex.release()

    while True:
        inputCmdLocal = raw_input('waiting input cmd: \n')
        if inputCmdLocal == 'exitguard':
            if g_mutex.acquire():
                g_CmdCode = 1
                g_mutex.release()
            break
        elif inputCmdLocal == 'killexit':
            if g_mutex.acquire():
                g_CmdCode = 2
                g_mutex.release()
            break
        time.sleep(1)
    if g_mutex.acquire():
        print threadname, ' ended.'
        g_mutex.release()

def main(args):
    #处理输入参数
    if len(args) != 1:
        return fail("configure file needed ")
    config = ConfigParser.ConfigParser()
    config.read(args)
    #单独运行的进程
    AloneServerCount = int( config.get('STAND_ALONE', 'SERVER_COUNT') )
    listAloneServerCmd = list()
    for i in range(0, AloneServerCount):
        serverIdx = 'SERVER_' + str(i)
        runCmd = config.get('STAND_ALONE', serverIdx)
        print 'SERVER_', i, ':', runCmd
        listAloneServerCmd.append( runCmd )

    #日志
    curTime = time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time()))
    logfname = time.strftime('%Y%m%d%H%M%S', time.localtime(time.time())) + '.log'
    fLog = open(logfname, 'w')
    LogString = curTime + '\n'
    fLog.write(LogString)
    print LogString
    
    global g_CmdCode, g_mutex
    #创建输入线程
    InputThread = threading.Thread(target=InputThreadMain, name = 'input_recv')
    InputThread.start()
    #单独运行：创建需要运行的进程
    mapServerProcess = dict()
    for runCmd in listAloneServerCmd:
        serverP = subprocess.Popen(runCmd)
	time.sleep(3)
        mapServerProcess[runCmd] = serverP
        #日志
        curTime = time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time()))
        LogString = '[' + curTime + ']' + runCmd + ', pid: ' + str(serverP.pid) + '\n'
        fLog.write(LogString)
        print LogString

    #运行状态检查
    while True:
        #单独运行的进程
        for runCmd, serverP in mapServerProcess.items():
            if serverP.poll() != None:
                #日志
                curTime = time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time()))
                LogString = '[' + curTime + ']' + 'trying restart:' + runCmd + '\n'
                fLog.write(LogString)
                if g_mutex.acquire():                    
                    print LogString
                    g_mutex.release()
                #
                time.sleep(5)
                serverP = subprocess.Popen(runCmd)
                #
                #日志
                curTime = time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time()))
                LogString = '[' + curTime + ']' + 'restarted:' + runCmd + ', Pid:' + str(serverP.pid) + '\n'
                fLog.write(LogString)
                if g_mutex.acquire():
                    print LogString
                    g_mutex.release()
                #更新map
                del mapServerProcess[runCmd]
                mapServerProcess[runCmd] = serverP
                fLog.flush()
                break

        #检查输入状态
        bExit = 0
        bKillAll = 0
        if g_mutex.acquire():
            if g_CmdCode == 1:
                bExit = 1
            elif g_CmdCode == 2:
                bKillAll = 1
            g_mutex.release()
        if bExit == 1:
            print 'exiting'
            break
        elif bKillAll == 1:
            print 'start kill process'
            for runCmd, serverP in mapServerProcess.items():
                kill(serverP.pid)
            break
        time.sleep(1)
        
    print 'process done'
    curTime = time.strftime('%Y-%m-%d:%H:%M:%S', time.localtime(time.time()))
    LogString = '[' + curTime + ']' + 'end' + '\n'
    fLog.write(LogString)
    fLog.close()
        
    return 0
                                
if __name__ == '__main__':
    args = sys.argv[1:]
    main(args)


