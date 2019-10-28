#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>

#include "usb_boot.h"
#include "XLink.h"
#define MAXNAMESIZE 28
#define FIP "/lib/firmware/myriad.mvcmd"


int main(int argc, char **argv)
{
    printf("POC for downloading FIP using XLink API.\n");
    char name[MAXNAMESIZE];
    int rc = XLinkGetDeviceName(0, name, sizeof(name));
    if (!rc)
    {
        printf("Device Found name %s \n", name);
    }
    else
    {
        printf("ERROR couldn't find devices rc %d\n", rc);
        exit(1);
    }
    XLinkGlobalHandler_t ghandler = {
        .protocol = USB_VSC,
    };
    XLinkHandler_t handler = {
#if defined(USE_USB_VSC)
        .devicePath = name,
#elif defined(USE_USB_CDC)
        .devicePath = "/dev/ttyACM0",
        .devicePath2 = "/dev/ttyACM1",
#elif defined(USE_PCIE)
        .devicePath = "/dev/ma2485_0",
#endif
    };
#ifndef BOOT_DISABLE
    printf("Booting " FIP "\n");
    if( XLinkBootRemote(name, FIP) != X_LINK_SUCCESS){
        printf("ERROR couldn't boot the device\n");
        exit(1);
    }
#endif
    printf("Myriad was booted\n");
    while(XLinkInitialize(&ghandler) != X_LINK_SUCCESS);
    printf("Initialize done\n");

    while(XLinkConnect(&handler) != X_LINK_SUCCESS);
    printf("XLinkConnect done - link Id %d\n", handler.linkId);

    XLinkError_t status;
    
    status = XLinkResetRemote(handler.linkId);
    if (status == 0)
    {
        printf("reset success\n");
    }
    else
    {
        printf("reset failed: %x\n", status);
    }

    exit(0);  // no errors

}

