from classes.avaspec import *
import time

ret = AVS_GetNrOfDevices()

if ret>0:
    ret = AVS_Init(0)
    mylist = AvsIdentityType()
    mylist = AVS_GetList(1)
    serial = str(mylist[0].SerialNumber.decode('utf-8'))

    print(serial)

    dev_handle = AVS_Activate(mylist[0])

    devcon = DeviceConfigType()
    devcon = AVS_GetParameter(dev_handle, 63484)

    pxl = devcon.m_Detector_m_NrPixels
    wavelength = AVS_GetLambda(dev_handle)

    ret = AVS_UseHighResAdc(dev_handle, True)
    measconfig = MeasConfigType()
    measconfig.m_StartPixel = 0
    measconfig.m_StopPixel = pxl - 1
    measconfig.m_IntegrationTime = 100
    measconfig.m_IntegrationDelay = 0
    measconfig.m_NrAverages = 1
    measconfig.m_CorDynDark_m_Enable = 0  # nesting of types does NOT work!!
    measconfig.m_CorDynDark_m_ForgetPercentage = 0
    measconfig.m_Smoothing_m_SmoothPix = 0
    measconfig.m_Smoothing_m_SmoothModel = 0
    measconfig.m_SaturationDetection = 0
    measconfig.m_Trigger_m_Mode = 1
    measconfig.m_Trigger_m_Source = 0
    measconfig.m_Trigger_m_SourceType = 0
    measconfig.m_Control_m_StrobeControl = 0
    measconfig.m_Control_m_LaserDelay = 0
    measconfig.m_Control_m_LaserWidth = 0
    measconfig.m_Control_m_LaserWaveLength = 785.0
    measconfig.m_Control_m_StoreToRam = 0
    print('Prepping for measurement')
    ret = AVS_PrepareMeasure(dev_handle, measconfig)

    scans = 0
    stopscanning = False
    while (stopscanning == False):
        ret = AVS_Measure(dev_handle, 0, 1)
        dataready = False
        while (dataready == False):
            dataready = (AVS_PollScan(dev_handle) == True)
            time.sleep(0.001)
        if dataready == True:
            scans = scans + 1
            if (scans >= 1):
                stopscanning = True
                    
        time.sleep(0.001)

    print('Data is ready')

    ret = AVS_GetScopeData(dev_handle)
    values_test = []
    x = 0
    while (x < pxl):
        values_test.append((round(wavelength[x],4), float(ret[1][x])))

        x += 1
    print(values_test)
else:
    print('No Avaspec connected')