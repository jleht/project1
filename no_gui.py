#!/usr/bin/env python3

from cProfile import label
import os
from datetime import datetime
import logging
from re import L
import coloredlogs
import pathlib
import sys
import time

from classes.check_serial import SerialConnection
from classes.Falcon import Falcon
from classes.teensy import Teensy
from classes import avaspec as spec
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import libs_metrics
from importlib import reload
import matplotlib

class Spec:
    def __init__(self, falcon:Falcon, tmc:Teensy, integrationTime: float = 0.03, integrationDelay: int = 0, nrAverages: int = 1, triggerMode: int = 1):
        _ = spec.AVS_Init()
        self.savePath = '{}/measurements'.format(
        pathlib.Path(__file__).parent)
        os.makedirs(self.savePath, exist_ok=True)
        if spec.AVS_GetNrOfDevices() > 0:
            mylist = spec.AvsIdentityType()
            mylist = spec.AVS_GetList(1)

            self.spec_handle = spec.AVS_Activate(mylist[0])
            devcon = spec.DeviceConfigType()
            devcon = spec.AVS_GetParameter(self.spec_handle, 63484)

            self.pixels = devcon.m_Detector_m_NrPixels
            self.wavelength = spec.AVS_GetLambda(self.spec_handle)

            ret = spec.AVS_UseHighResAdc(self.spec_handle, True)

            self.measconfig = spec.MeasConfigType()
            self.measconfig.m_StartPixel = 0
            self.measconfig.m_StopPixel = self.pixels - 1
            self.measconfig.m_IntegrationTime = integrationTime
            self.measconfig.m_IntegrationDelay = integrationDelay
            self.measconfig.m_NrAverages = nrAverages
            self.measconfig.m_Trigger_m_Mode = triggerMode

            self.falcon = falcon
            self.tmc = tmc

            self.header_text = ''

            self.csvHeader()
            time.sleep(0.1)
            self.falcon.sendCmd('dfreq 10')
            self.falcon.sendCmd('qsdelay 201')

            plt.ion()

        else:
            logging.critical('No Avantes Spectrometer found')
            sys.exit(0)
        
        self.is_shown = False
        self.highest_intensity = pd.DataFrame(np.zeros(4094,))
        self.current_intensities = []
        self.spec_wavelengths = [x for x in spec.AVS_GetLambda(self.spec_handle)][:-2]
        self.count = 0

    def configureSpec(self, integrationTime: float = 0.03, integrationDelay: int = 0, nrAverages: int = 1, triggerMode: int = 1):
        self.measconfig.m_IntegrationTime = integrationTime
        self.measconfig.m_IntegrationDelay = integrationDelay
        self.measconfig.m_NrAverages = nrAverages
        self.measconfig.m_Trigger_m_Mode = triggerMode

    def startMeasurement(self, count: int = 1):
        if self.falcon.is_online():
            results = []
            ret = spec.AVS_PrepareMeasure(self.spec_handle, self.measconfig)
            scans = 0
            scanning = True
            fired = False

            # Sending a command to the wanted ammount + 5 (q-switch requires this)
            self.falcon.sendCmd('burst {:d}'.format(count+5))

            while scanning:
                logging.info('Starting measurement')
                ret = spec.AVS_Measure(self.spec_handle, 0, 1)
                dataready = False
                time.sleep(0.01)
                if not fired:
                    self.falcon.sendCmd('fire')
                    fired = True

                while dataready == False:
                    dataready = (spec.AVS_PollScan(self.spec_handle) == True)
                    time.sleep(0.001)
                if dataready == True:
                    scans = scans + 1
                    if scans >= count:
                        scanning = False

                    logging.info('Data measured')
                    ret = spec.AVS_GetScopeData(self.spec_handle)
                    x = 0
                    values = {'wavelength': [], 'intensity': []}


                    while (x < self.pixels):
                        values['wavelength'].append(round(self.wavelength[x], 4))
                        values['intensity'].append(float(ret[1][x]))
                        x += 1
                    

                    df = pd.DataFrame(data=values)

                    self.current_intensities.append(df['intensity'])
                    if int(df['intensity'].max()) > int(self.highest_intensity.max()):
                        self.highest_intensity = df['intensity']

                    logging.info('Max intensity: {}'.format(df['intensity'].max()))
                    dtnow = datetime.now().strftime('%Y-%m-%d-%H_%M_%S_%f')
                    filepath = '{}/{}_{:04d}.csv'.format(self.savePath,dtnow, scans)
                    f = open(filepath,'wb')
                    f.write(self.header_text)
                    f.close()
                    df.to_csv(filepath, index=False, mode='a')

                    filepath2 = '{}/latest.csv'.format(self.savePath)
                    df.to_csv(filepath2, index=False)

                time.sleep(0.001)
            self.make_plot([values['wavelength'],values['intensity']])
            #self.make_plot([values['wavelength'],self.highest_intensity])
        else:
            logging.error('Falcon control box is offline.')
    
    def measureDarkness(self, count:int = 1):
        results = []
        ret = spec.AVS_PrepareMeasure(self.spec_handle, self.measconfig)
        scans = 0
        scanning = True

        while scanning:
            logging.info('Starting measurement')
            ret = spec.AVS_Measure(self.spec_handle, 0, 1)
            dataready = False
            time.sleep(0.01)
            while dataready == False:
                dataready = (spec.AVS_PollScan(self.spec_handle) == True)
                time.sleep(0.001)
            if dataready == True:
                
                logging.info('Data measured')
                ret = spec.AVS_GetScopeData(self.spec_handle)
                x = 0
                values = {'wavelength': [], 'intensity': []}
                while (x < self.pixels):
                    values['wavelength'].append(round(self.wavelength[x], 4))
                    values['intensity'].append(float(ret[1][x]))
                    x += 1

                df = pd.DataFrame(data=values)
                filepath = '{}/dark.csv'.format(self.savePath)
                f = open(filepath,'wb')
                f.write(self.header_text)
                f.close()
                df.to_csv(filepath, index=False, mode='a')
                scanning = False


            time.sleep(0.001)

    def darknessBatch(self, count, step):
        while count>0:
            count -= 1
            results = []
            ret = spec.AVS_PrepareMeasure(self.spec_handle, self.measconfig)
            scans = 0
            scanning = True

            while scanning:
                logging.info('Starting measurement')
                ret = spec.AVS_Measure(self.spec_handle, 0, 1)
                dataready = False
                time.sleep(0.04)
                while dataready == False:
                    dataready = (spec.AVS_PollScan(self.spec_handle) == True)
                    time.sleep(0.001)
                if dataready == True:
                    scans = scans + 1
                    if scans >= 5:
                        scanning = False
                    logging.info('Data measured')
                    ret = spec.AVS_GetScopeData(self.spec_handle)
                    x = 0
                    values = {'wavelength': [], 'intensity': []}
                    while (x < self.pixels):
                        values['wavelength'].append(round(self.wavelength[x], 4))
                        values['intensity'].append(float(ret[1][x]))
                        x += 1

                    df = pd.DataFrame(data=values)
                    dtnow = datetime.now().strftime('%Y-%m-%d-%H_%M_%S_%f')
                    filepath = filepath = '{}/dark_{}_{:04d}.csv'.format(self.savePath,dtnow, scans)
                    f = open(filepath,'wb')
                    f.write(self.header_text)
                    f.close()
                    df.to_csv(filepath, index=False, mode='a')
                    time.sleep(0.04)    

    def grid(self, count:int = 1, shots:int = 5, step:int = -100):
        if self.falcon.is_online():
            while count>0:
                count -= 1
                self.tmc.move_axis('x{}'.format(step))
                self.startMeasurement(shots)
        else:
            logging.error('Falcon control box is offline.')

    def setSpecValues(self):
        integrationTime = input('Enter integration time in ms (default: 0.03ms): ').strip().lower()
        integrationDelay = input('Enter FPGA cycle count for integration delay (default: 0)').strip().lower()
        nrAverages = input('Enter the amount to average together (default: 1): ').strip().lower()
        triggerMode = input('Set trigger mode (default: 1): ').strip().lower()

        integrationTime = 0.03 if integrationTime == '' else float(integrationTime)
        integrationDelay = 0 if integrationDelay == '' else int(integrationDelay)
        nrAverages = 1 if nrAverages == '' else int(nrAverages)
        triggerMode = 1 if triggerMode == '' else int(triggerMode)


        self.configureSpec(integrationTime=integrationTime,integrationDelay=integrationDelay, nrAverages=nrAverages,triggerMode=triggerMode)

    def csvHeader(self):
        if self.falcon.is_online():
            dfreq = self.falcon.sendCmd('DFREQ ?')[0].decode().strip()
            burst = self.falcon.sendCmd('BURST ?')[0].decode().strip()
            qsblank = self.falcon.sendCmd('QSBLANK ?')[0].decode().strip()
            qsdelay = self.falcon.sendCmd('QSDELAY ?')[0].decode().strip()
            qspre = self.falcon.sendCmd('QSPRE ?')[0].decode().strip()

            output = 'Laser settings:\n\tDiode frequency:\t{} Hz\n\tPulses fired:\t\t{}\n\tQ-Switch blanking:\t{}\n\tQ-Switch delay:\t\t{} \u03BCs\n\tQ-Switch presync:\t{} \u03BCs\n'
            output = output.format(dfreq[7:], burst[7:], qsblank[9:], qsdelay[9:], qspre[7:])

            output += 'Spectrometer settings:\n\tIntegration time:\t{:.04f} ms\n\tIntegration delay:\t{:.3f} ns\n\tAveraging:\t\t{}\n\tTrigger mode:\t\t{}\n\n\n'
            output = output.format(self.measconfig.m_IntegrationTime,(self.measconfig.m_IntegrationDelay*20.83), self.measconfig.m_NrAverages, 'External' if self.measconfig.m_Trigger_m_Mode == 1 else 'Internal')

            self.header_text = output.encode('utf-8')
        else:
            logging.error('Falcon control box is offline.')
        
    def autofocus(self):
        if self.falcon.is_online():

            startNow = input('Start from current position? (y/N): ').lower()
            
            findingFocus = True
            lastIntensity = 0
            hiIntensity = 0
            lastMovement = 0

            if startNow == 'n' or startNow=='':
                self.tmc.move_axis('z0')
            
            count = 3
            # Sending a command to the wanted ammount + 5 (q-switch requires this)
            self.falcon.sendCmd('burst {:d}'.format(count+5))

            while findingFocus:
                avg_intensity = 0
                ret = spec.AVS_PrepareMeasure(self.spec_handle, self.measconfig)
                scans = 0
                scanning = True
                fired = False
                while scanning:
                    logging.debug('Starting measurement')
                    ret = spec.AVS_Measure(self.spec_handle, 0, 1)
                    dataready = False
                    time.sleep(0.01)
                    if not fired:
                        self.falcon.sendCmd('fire')
                        fired = True

                    while dataready == False:
                        dataready = (spec.AVS_PollScan(self.spec_handle) == True)
                        time.sleep(0.001)
                    if dataready == True:
                        scans = scans + 1
                        if scans >= count:
                            scanning = False

                        logging.debug('Data measured')
                        ret = spec.AVS_GetScopeData(self.spec_handle)
                        x = 0
                        values = {'wavelength': [], 'intensity': []}

                        while (x < self.pixels):
                            values['wavelength'].append(round(self.wavelength[x], 4))
                            values['intensity'].append(float(ret[1][x]))
                            x += 1

                        df = pd.DataFrame(data=values)
                        
                        self.current_intensities.append(df['intensity'])

                        avg_intensity += df['intensity'].max()


                    time.sleep(0.001)

                avg_intensity = avg_intensity/count
                logging.info('\nLast intensity: {:0.2f}\tAvg. intensity: {:0.2f}\tHi intensity: {:0.2f}'.format(lastIntensity,avg_intensity,hiIntensity))
                self.make_plot([values['wavelength'],values['intensity']])

                if hiIntensity<avg_intensity:
                    hiIntensity = avg_intensity
                    future_z = 0

                if (lastIntensity > avg_intensity) and (hiIntensity>1500) and (hiIntensity*0.85>avg_intensity):
                    findingFocus = False
                    self.tmc.move_axis('z{}'.format(future_z))
                else:
                    lastIntensity = avg_intensity
                    self.tmc.move_axis('x-50')
                    if avg_intensity<1500:
                        lastMovement = 100*4
                    elif avg_intensity>1500 and avg_intensity<4000:
                        lastMovement = 50*4
                    else:
                        lastMovement = 25*4

                    if avg_intensity>1000:
                        count = 5
                        # Sending a command to the wanted ammount + 5 (q-switch requires this)
                        self.falcon.sendCmd('burst {:d}'.format(count+5))
                    
                    future_z += lastMovement

                    self.tmc.move_axis('z{}'.format(-lastMovement))
                

        else:
            logging.error('Falcon control box is offline.')
    
    def plot_all_as_img(self):
        matplotlib.use('Agg')
        font = {'family' : 'normal',
                'weight' : 'bold',
                'size' : 52}
        plt.ioff
        filenames = []
        existing_imgs = []
        if not os.path.exists('./plot_images'):
            os.makedirs('./plot_images')
        for file in os.listdir('./measurements'):
            if file.endswith('.csv'):
                filenames.append(file)
        for file in os.listdir('./plot_images'):
            if file.endswith('.png'):
                existing_imgs.append(file[:-3])
        for name in filenames:
            found = False
            if name[:-3] in existing_imgs:
                continue
            else:
                with open('./measurements/'+name) as readfile:
                    for cnt, line in enumerate(readfile):
                        if "wavelength,intensity" in line:
                            row_num = cnt
                            found = True
                if not found:continue
                readfile.close
                df = pd.read_csv('./measurements/'+name, skiprows=row_num)
                fig = plt.figure(figsize=(50,40))
                plt.rc('xtick',labelsize=42)
                plt.rc('ytick',labelsize=42)
                plt.rc('axes', labelsize=52)
                plt.xlabel('Wavelength')
                plt.ylabel('Intensity')
                plt.ylim((0,60000))
                plt.plot(df['wavelength'], df['intensity'])
                plt.savefig('./plot_images/'+name[:-4]+'.png')
                plt.close(fig)
                #df.plot(figsize=(50,40), x='wavelength', y='intensity', ylim=(0,35000)).get_figure().savefig('./plot_images/'+name[:-4]+'.png')
        plt.ion()
        matplotlib.use('QtAgg')
    def search_params(self,):
        if self.falcon.is_online():

            hiIntensity = 0
            self.falcon.sendCmd('QSPRE 0')
            presync = 0
            
            count = 3
            # Sending a command to the wanted ammount + 5 (q-switch requires this)
            self.falcon.sendCmd('burst {:d}'.format(count+5))

            while presync < 33:
                avg_intensity = 0
                ret = spec.AVS_PrepareMeasure(self.spec_handle, self.measconfig)
                scans = 0
                scanning = True
                fired = False
                while scanning:
                    logging.debug('Starting measurement')
                    ret = spec.AVS_Measure(self.spec_handle, 0, 1)
                    dataready = False
                    time.sleep(0.01)
                    if not fired:
                        self.falcon.sendCmd('fire')
                        fired = True

                    while dataready == False:
                        dataready = (spec.AVS_PollScan(self.spec_handle) == True)
                        time.sleep(0.001)
                    if dataready == True:
                        scans = scans + 1
                        if scans >= count:
                            scanning = False

                        logging.debug('Data measured')
                        ret = spec.AVS_GetScopeData(self.spec_handle)
                        x = 0
                        values = {'wavelength': [], 'intensity': []}

                        while (x < self.pixels):
                            values['wavelength'].append(round(self.wavelength[x], 4))
                            values['intensity'].append(float(ret[1][x]))
                            x += 1

                        df = pd.DataFrame(data=values)
                        
                        self.current_intensities.append(df['intensity'])

                        avg_intensity += df['intensity'].max()


                    time.sleep(0.001)

                avg_intensity = avg_intensity/count
                self.make_plot([values['wavelength'],values['intensity']])

                if hiIntensity<avg_intensity:
                    hiIntensity = avg_intensity
                    best_presync = presync
                logging.info('\n\tAvg. intensity: {:0.2f}\tHi intensity: {:0.2f}'.format(avg_intensity,hiIntensity))

                self.tmc.move_axis('x-100')                
                presync += 1
                self.falcon.sendCmd('QSPRE {}'.format(presync))
                time.sleep(0.01)
            print('Highest intensity presync {}'.format(best_presync))
        else:
            logging.error('Falcon control box is offline.')

    def get_metrics(self):
        reload(libs_metrics)
        if len(self.current_intensities) > self.count:
            libs_metrics.group_shots(self.current_intensities,self.count)
        else:
            libs_metrics.single_group(self.current_intensities, self.count)

    def make_plot(self, data):
        matplotlib.use('QtAgg')
        mngr = plt.get_current_fig_manager()
        geom = mngr.window.geometry()
        x,y,dx,dy = geom.getRect()
        mngr.window.setGeometry(940,520,600,400)
        plt.clf()
        plt.ylim(0,60000)
        plt.rcParams["figure.figsize"] = 12,10
        plt.rc('xtick',labelsize=4)
        plt.rc('ytick',labelsize=4)
        plt.rc('axes', labelsize=2)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.plot(data[0],data[1])
        plt.pause(0.001)
        plt.show()

if __name__ == '__main__':
    level = logging.INFO
    fmt = '[ %(asctime)s :: %(levelname)s ] %(message)s'
    coloredlogs.install(level=level, fmt=fmt)
    logging.basicConfig(level=level, format=fmt)

    cs = SerialConnection()
    teensy_port = cs.find_machine(0x1209, 0xAD10)
    falcon_port = cs.find_machine(0x067b, 0x2303)

    if teensy_port:
        tmc = Teensy(teensy_port)

    if falcon_port:
        falcon = Falcon(falcon_port)

    sp = Spec(tmc=tmc, falcon=falcon)
    input_stream = ''
    output = 0
    running = True
    while running:
        sp.highest_intensity = pd.DataFrame(np.zeros(4094,))
        sp.current_intensities = []
        try:
            output = 0
            input_stream = input('Please enter command: ').strip().lower()

            if input_stream == 'status':
                if falcon.is_online():
                    falcon.getStatus()
                    output = 0
                else:
                    logging.error('Falcon control box is offline.')
            elif input_stream[0:4] == 'fire':
                meas_count = input_stream[4:]
                if meas_count == '':
                    sp.count = 1
                else:
                    sp.count = int(meas_count)

                sp.startMeasurement(sp.count)
                sp.get_metrics()
            elif input_stream == 'dark':
                sp.configureSpec(triggerMode=0)
                sp.csvHeader()
                sp.measureDarkness()
            elif input_stream[0:4] == 'move':
                cmd = input_stream[4:].strip()
                tmc.move_axis(cmd)
            elif input_stream == 'posx':
                output = tmc.get_axis_position('x')
            elif input_stream == 'posz':
                output = tmc.get_axis_position('z')
            elif input_stream == 'config':
                sp.setSpecValues()
                sp.csvHeader()
            elif input_stream[0:4] == 'grid':
                count = input_stream.split()[1]
                shots = int(input_stream.split()[2])
                if count == '':
                    count = 1
                else:
                    count = int(count)
                sp.count = shots
                sp.grid(count,shots)
                sp.get_metrics()
            elif input_stream[0:13] == 'darknessbatch':
                sp.configureSpec(triggerMode=0)
                count = input_stream[13:]
                if count == '':
                    count = 1
                else:
                    count = int(count)

                sp.darknessBatch(count, -100)
            elif input_stream in ('quit', 'exit'):
                output = ['Quitting...'.encode()]
                running = False
            elif input_stream[0:2] == 'f_':
                cmd = input_stream[2:]
                logging.debug(cmd)
                output = falcon.sendCmd(cmd)
                sp.csvHeader()
            elif input_stream == 'csv':
                sp.csvHeader()
                print(sp.header_text.decode())
            elif input_stream == 'autofocus':
                sp.autofocus()
                #sp.get_metrics()
            elif input_stream == 'qspre_search':
                sp.search_params()
            elif input_stream == 'plot':
                sp.plot_all_as_img()
            else:
                output = []
                msg = 'Unknown command: {}'.format(input_stream)
                output.append(msg.encode())

            if not isinstance(output, int):
                for msg in output:
                    logging.info(msg.decode())
        except (KeyboardInterrupt, Exception) as b:
            if isinstance(b,KeyboardInterrupt):
                logging.error('Keyboard interrupt')
            else:
                logging.error(b)
