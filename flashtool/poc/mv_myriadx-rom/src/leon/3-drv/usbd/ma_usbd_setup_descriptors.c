/*
 * {% copyright %}
 */

/**
 * @brief     Defines the various descriptors and provides the setup function to initialise the RAM copies
 */

#include <soc_def.h>
#include <stdint.h>
#include "ma_usbd_common.h"
#include "ma_usbd_internal.h"

/* Declare our ROM-based device and configuration descriptors */
static const uint8_t usbd_desc_device_rom[USB_DESC_ROUND_SZ(USB_DESCSZ_DEVICE)];
static const uint8_t usbd_desc_config_start_rom[USB_DESCSZ_CONFIG + USB_DESCSZ_INTERFACE + USB_DESCSZ_ENDPOINT];
static const uint8_t usbd_desc_config_usb3compan_rom[USB_DESCSZ_SS_EP_COMPANION];
static const uint8_t usbd_desc_config_ep1_rom[USB_DESCSZ_ENDPOINT];
static const uint8_t usbd_desc_dev_qualifier_rom[USB_DESC_ROUND_SZ(USB_DESCSZ_DEV_QUALIFIER)];
static const uint8_t usbd_desc_otherspeed_cfg_rom[USB_DESC_ROUND_SZ(USBD_DESCSZ_OTHERSPEED_IFACE_EP)];
static const uint8_t usbd_desc_wincompatid_rom[USB_DESC_ROUND_SZ(USBD_DESCSZ_WINCOMPATID)];
static const uint8_t usbd_desc_bos_rom[USB_DESC_ROUND_SZ(USBD_DESCSZ_BOS)];

/* Fill in the ROM-based device descriptor */
static const uint8_t usbd_desc_device_rom[] = {
	USB_DESCSZ_DEVICE,               /* bLength */
	USB_DESCTYPE_DEVICE,             /* bDescriptorType */
	PW(USB_DEVICE_DESC_USBVER_USB2), /* pdUSB */
	USBD_DEV_CLASS,                  /* pDeviceClass */
	USBD_DEV_SUBCLASS,               /* bDeviceSubClass */
	USBD_DEV_PROTOCOL,               /* bDeviceProtocol */
	USBD_EP0_SIZE,                   /* bMaxPacketSize0 */
	PW(USBD_VID_INTEL),              /* idVendor */
	PW(USBD_PID_KEEMBAY_ROM),        /* idProduct */
	PW(USBD_DEVICE_ID),              /* bcdDevice */
	USBD_STRIND_MANUFACTURER,        /* iManufacturer */
	USBD_STRIND_PRODUCT,             /* iProduct */
	USBD_STRIND_SERIALNUM,           /* iSerialNumber */
	USBD_NUM_CONFIGS,                /* bNumConfigurations */
};

/* Fill in the ROM-based configuration descriptor */
static const uint8_t usbd_desc_config_start_rom[] = {
	/* Configuration descriptor */
	USB_DESCSZ_CONFIG,                  /* bLength */
	USB_DESCTYPE_CONFIG,                /* bDescriptorType */
	PW(USBD_DESCSZ_CONF_IFACE_EP_USB2), /* wTotalLength */
	USBD_INTERFACE_COUNT,               /* bNumInterfaces */
	USBD_CONFIG0_ID,                    /* bConfigurationValue */
	USBD_STRIND_CONFIG0,                /* iConfiguration */
	USB_DEVDESC_ATTR_ALWAYS |
	USBD_CONFIG0_ATTRIBUTES,            /* bAttributes */
	(USBD_CONFIG0_MAXPOWER_MA / 2),     /* bMaxPower (units of 2mA) */
	/* interface descriptor */
	USB_DESCSZ_INTERFACE,               /* bLength */
	USB_DESCTYPE_INTERFACE,             /* bDescriptorType */
	USBD_INTERFACE0_ID,                 /* bInterfaceNumber */
	USBD_INTERFACE0_ALT,                /* bAlternateSetting */
	USBD_EP_BULK_CNT,                   /* bNumEndpoints */
	USBD_INTERFACE0_CLASS,              /* bInterfaceClass */
	USBD_INTERFACE0_SUBCLASS,           /* bInterfaceSubClass */
	USBD_INTERFACE0_PROTOCOL,           /* bInterfaceProtocol */
	USBD_STRIND_INTERFACE0,             /* iInterface */
	/* Endpoint descriptor - EP2 IN (EP5) */
	USB_DESCSZ_ENDPOINT,                /* bLength */
	USB_DESCTYPE_ENDPOINT,              /* bDescriptorType */
	USB_EP_PHYS2LOG(USBD_EP_BULK_IN),   /* bEndpointAddress */
	USB_EPDESC_ATTR_XFERTYP(USB_EPDESC_XFERTYP_BULK),
					    /* bmAttributes (2 = BULK) */
	PW(USBD_EP_BULK_IN_SIZE),           /* wMaxPacketSize */
	USBD_EP_BULK_IN_POLL_INTERVAL,      /* bInterval */
};

static const uint8_t usbd_desc_config_usb3compan_rom[] = {
	/* SuperSpeed USB Endpoint Companion descriptor */
	USB_DESCSZ_SS_EP_COMPANION,	/* bLength */
	USB_DESCTYPE_SS_EP_COMPANION,	/* bDescriptorType */
	0,				/* bMaxBurst */
	0,				/* bmAttributes */
	PW(0),				/* wBytesPerInterval */
};

static const uint8_t usbd_desc_config_ep1_rom[] = {
	/* Endpoint descriptor - EP1 OUT (EP2) */
	USB_DESCSZ_ENDPOINT,                /* bLength */
	USB_DESCTYPE_ENDPOINT,              /* bDescriptorType */
	USB_EP_PHYS2LOG(USBD_EP_BULK_OUT),  /* bEndpointAddress */
	USB_EPDESC_ATTR_XFERTYP(USB_EPDESC_XFERTYP_BULK),
					    /* bmAttributes (2 = BULK) */
	PW(USBD_EP_BULK_OUT_SIZE),          /* wMaxPacketSize */
	USBD_EP_BULK_OUT_POLL_INTERVAL,     /* bInterval */
};

/* Fill in the ROM-based device qualifier descriptor */
static const uint8_t usbd_desc_dev_qualifier_rom[] = {
	USB_DESCSZ_DEV_QUALIFIER,           /* bLength */
	USB_DESCTYPE_DEV_QUALIFIER,         /* bDescriptorType */
	PW(USB_DEVICE_DESC_USBVER_USB2),    /* pdUSB */
	USBD_DEV_CLASS,                     /* pDeviceClass */
	USBD_DEV_SUBCLASS,                  /* bDeviceSubClass */
	USBD_DEV_PROTOCOL,                  /* bDeviceProtocol */
	USBD_EP0_SIZE,                      /* bMaxPacketSize0 */
	USBD_NUM_CONFIGS,                   /* bNumConfigurations */
	0                                   /* bReserved */
};

/* Fill in the ROM-based other-speed configuration descriptor */
static const uint8_t usbd_desc_otherspeed_cfg_rom[] = {
	USB_DESCSZ_OTHERSPEED_CFG,          /* bLength */
	USB_DESCTYPE_OTHERSPEED_CFG,        /* bDescriptorType */
	PW(USBD_DESCSZ_OTHERSPEED_IFACE_EP),/* wTotalLength */
	USBD_INTERFACE_COUNT,               /* bNumInterfaces */
	USBD_CONFIG0_ID,                    /* bConfigurationValue */
	USBD_STRIND_CONFIG0,                /* iConfiguration */
	USB_DEVDESC_ATTR_ALWAYS |
	USBD_CONFIG0_ATTRIBUTES,            /* bAttributes */
	(USBD_CONFIG0_MAXPOWER_MA / 2),     /* bMaxPower (units of 2mA) */
	/* interface descriptor */
	USB_DESCSZ_INTERFACE,               /* bLength */
	USB_DESCTYPE_INTERFACE,             /* bDescriptorType */
	USBD_INTERFACE0_ID,                 /* bInterfaceNumber */
	USBD_INTERFACE0_ALT,                /* bAlternateSetting */
	USBD_EP_BULK_CNT,                   /* bNumEndpoints */
	USBD_INTERFACE0_CLASS,              /* bInterfaceClass */
	USBD_INTERFACE0_SUBCLASS,           /* bInterfaceSubClass */
	USBD_INTERFACE0_PROTOCOL,           /* bInterfaceProtocol */
	USBD_STRIND_INTERFACE0,             /* iInterface */
	/* Endpoint descriptor - EP2 IN (EP5) */
	USB_DESCSZ_ENDPOINT,                /* bLength */
	USB_DESCTYPE_ENDPOINT,              /* bDescriptorType */
	USB_EP_PHYS2LOG(USBD_EP_BULK_IN),   /* bEndpointAddress */
	USB_EPDESC_ATTR_XFERTYP(USB_EPDESC_XFERTYP_BULK),
					    /* bmAttributes (2 = BULK) */
	PW(USBD_EP_BULK_IN_SIZE_FS),        /* wMaxPacketSize */
	USBD_EP_BULK_IN_POLL_INTERVAL,      /* bInterval */
	/* Endpoint descriptor - EP1 OUT (EP2) */
	USB_DESCSZ_ENDPOINT,                /* bLength */
	USB_DESCTYPE_ENDPOINT,              /* bDescriptorType */
	USB_EP_PHYS2LOG(USBD_EP_BULK_OUT),  /* bEndpointAddress */
	USB_EPDESC_ATTR_XFERTYP(USB_EPDESC_XFERTYP_BULK),
					    /* bmAttributes (2 = BULK) */
	PW(USBD_EP_BULK_OUT_SIZE_FS),       /* wMaxPacketSize */
	USBD_EP_BULK_OUT_POLL_INTERVAL,     /* bInterval */
};

static const uint8_t usbd_desc_wincompatid_rom[] = {
	PD(USBD_DESCSZ_WINCOMPATID),        /* dw_length */
	PW(0x0100),                         /* bcdVersion */
	PW(0x0004),                         /* w_index - extended compatible ID */
	1,                                  /* bCount */
	0, 0, 0, 0, 0, 0, 0,                /* reserved */

	0,                                  /* bFirstInterfaceNumber */
	0x01,                               /* reserved (docs say 1 in examples) */
	0x57, 0x49, 0x4E, 0x55, 0x53, 0x42, 0x00, 0x00,     /* compatibleID - "WINUSB" */
	0, 0, 0, 0, 0, 0, 0, 0,             /* subCompatibleID */
	0, 0, 0, 0, 0, 0,                   /* reserved */
};

static const uint8_t usbd_desc_bos_rom[] = {
	/* Binary Object Store (BOS) Descriptor */
	USB_DESCSZ_BOS,			/* bLength */
	USB_DESCTYPE_BOS,		/* bDescriptorType */
	PW(USBD_DESCSZ_BOS),		/* wTotalLength */
	2,				/* bNumDeviceCaps */
	/* USB 2.0 Extension Descriptor */
	USB_DESCSZ_DEVCAP_USB2EXTENSION,	/* bLength */
	USB_DESCTYPE_DEVICE_CAPABILITY,		/* bDescriptorType */
	USB_DEVCAP_DESC_TYPE_USB2EXTENSION,	/* bDevCapabilityType */
	PD(0x02),		/* bmAttributes */
				/* LPMCapable           : 1 (Link Power Management protocol is supported) */
				/* BESLAndAlternateHIRD : 0 (BESL & Alternate HIRD definitions are not supported) */
				/* BaselineBESLValid    : 0 (not valid) */
				/* DeepBESLValid        : 0 (not valid) */
				/* BaselineBESL         : 0 */
				/* DeepBESL             : 0 */
	/* SuperSpeed USB Device Capability Descriptor */
	USB_DESCSZ_DEVCAP_SUPERSPEEDUSB,	/* bLength */
	USB_DESCTYPE_DEVICE_CAPABILITY,		/* bDescriptorType */
	USB_DEVCAP_DESC_TYPE_SUPERSPEEDUSB,	/* bDevCapabilityType */
	0x00,					/* bmAttributes (LTM support) */
	PW(0x0e),				/* wSpeedsSupported (Full-Speed, High-Speed, SuperSpeed) */
	0x01,					/* bFunctionalitySupport (lowest speed is 'full-speed') */
	0x0a,					/* bU1DevExitLat (less than 10 us) */
	PW(0x07ff),				/* wU2DevExitLat (less than 2047 us) */
};

/* make sure we only have one copy of each in ROM as we use these multiple times. */
static const char usbd_str2_str[] = USBD_STR2_STR;
static const char usbd_str2_oem_str[] = USBD_STR2_OEM_STR;

/* Build a string descriptor, expanding an 8-bit string into a 16-bit string. */
static void fill_str_desc(uint8_t *buff, uint16_t buff_size, const char *str, uint8_t str_len)
{
	uint8_t *ep = buff + buff_size;

	*buff++ = 2 + (2 * str_len);
	*buff++ = USB_DESCTYPE_STRING;
	while (str_len--) {
		*((uint16_t *)buff) = (uint8_t)(*str++);
		buff += 2;
	}
	while (buff < ep) {
		*buff++ = 0;
	}
}

// static void int2hex16(char *p, uint16_t val)
// {
// 	int i;

// 	p += 3;
// 	for (i = 0; i < 8; i++) {
// 		uint8_t n = val & 0xf;

// 		if (n >= 10)
// 			*p = n + ('a' - 10);
// 		else
// 			*p = n + '0';
// 		val >>= 4;
// 		p--;
// 	}
// }

static inline void *winprop_build_head(void)
{

	uintptr_t usbd_win_state = (uintptr_t)usbd_state_ptr->usbd_desc_winprop;

	*((uint32_t *)((uint32_t *)usbd_win_state + 0)) = USBD_DESC_WINPROP_HEADERSZ; /* dw_length */
	*((uint16_t *)((uint32_t *)usbd_win_state + 4)) = 0x0100;                    /* bcdVersion */
	*((uint16_t *)((uint16_t *)usbd_win_state + 6)) = 0x0005;                    /* w_index - extended properties */
	*((uint16_t *)((uint16_t *)usbd_win_state + 8)) = 0;                         /* wCount (will be incremented) */
	return (void *)(usbd_state_ptr->usbd_desc_winprop + USBD_DESC_WINPROP_HEADERSZ);
}

static void *winprop_build_prop_size(void *_ptr, const char *name, uint32_t name_size,
				     const char *val, uint32_t val_size)
{
	uint32_t propsize = USBD_DESC_WINPROP_PROPSTRUCT_SIZE + (name_size * 2) + (val_size * 2);

	uintptr_t usbd_win_state = (uintptr_t)usbd_state_ptr->usbd_desc_winprop;

	(*((uint32_t *)((uint32_t *)usbd_win_state + 0))) += propsize;   /* (header) dw_length */
	(*((uint16_t *)((uint16_t *)usbd_win_state + 8)))++;           /* (header) wCount */

	uint16_t *ptr = (uint16_t *)_ptr;

	ptr[0] = (uint16_t)(propsize >>  0); /* dwSize */
	ptr[1] = (uint16_t)(propsize >> 16);
	ptr[2] = 0x0001;                   /* dwPropertyDataType - REG_SZ */
	ptr[3] = 0;
	ptr[4] = name_size * 2;              /* wPropertyNameLength */
	ptr += 5;
	while (name_size--) {
		/* bPropertyName */
		*ptr++ = (uint8_t)(*name++);
	}
	*ptr++ = (uint16_t)((val_size * 2) >>  0); /* dwPropertyDataLength */
	*ptr++ = (uint16_t)((val_size * 2) >> 16);
	while (val_size--) {
		/* bPropertyData */
		*ptr++ = (uint8_t)(*val++);
	}
	return (void *)ptr;
}

/* Copy or build the required descriptors in RAM, modifying them if necessary.
 * Set pointers and sizes in the global driver state.
 */
void usbd_setup_descriptors(const ma_usb_config_t * const cfg)
{
	uint16_t vid = cfg->id_vendor;
	uint16_t pid = cfg->id_product;
	uint8_t str_ind = cfg->usbd_stri;
	uint8_t en_winusb = cfg->usbd_windis;

	/* TODO update with proper fix for USB3 */
	UNUSED(usbd_desc_config_usb3compan_rom);

	memcpy(usbd_state_ptr->usbd_desc_device, usbd_desc_device_rom, sizeof(usbd_desc_device_rom));
	usbd_state_ptr->desc_device.ptr = (void *)usbd_state_ptr->usbd_desc_device;
	usbd_state_ptr->desc_device.size = USB_DESCSZ_DEVICE;
	if (vid != 0) {
		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IDVENDOR + 0] = (vid >> 0) & 0xff;
		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IDVENDOR + 1] = (vid >> 8) & 0xff;
	} else
		vid = USBD_VID_INTEL;
	if (pid != 0) {
		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IDPRODUCT + 0] = (pid >> 0) & 0xff;
		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IDPRODUCT + 1] = (pid >> 8) & 0xff;
	} else {
		pid = USBD_PID_KEEMBAY_ROM;
	}

	memcpy(usbd_state_ptr->usbd_desc_config, usbd_desc_config_start_rom, sizeof(usbd_desc_config_start_rom));
	memcpy(usbd_state_ptr->usbd_desc_config + sizeof(usbd_desc_config_start_rom),
		usbd_desc_config_ep1_rom, sizeof(usbd_desc_config_ep1_rom));
	usbd_state_ptr->desc_config.ptr = (void *)usbd_state_ptr->usbd_desc_config;
	usbd_state_ptr->desc_config.size = USBD_DESCSZ_CONF_IFACE_EP_USB2;

	memcpy(usbd_state_ptr->usbd_desc_dev_qualifier,
		usbd_desc_dev_qualifier_rom, sizeof(usbd_desc_dev_qualifier_rom));
	usbd_state_ptr->desc_dev_qualifier.ptr = (void *)usbd_state_ptr->usbd_desc_dev_qualifier;
	usbd_state_ptr->desc_dev_qualifier.size = USB_DESCSZ_DEV_QUALIFIER;

	memcpy(usbd_state_ptr->usbd_desc_otherspeed_cfg, usbd_desc_otherspeed_cfg_rom,
		sizeof(usbd_desc_otherspeed_cfg_rom));
	usbd_state_ptr->desc_otherspeed_cfg.ptr = (void *)usbd_state_ptr->usbd_desc_otherspeed_cfg;
	usbd_state_ptr->desc_otherspeed_cfg.size = USBD_DESCSZ_OTHERSPEED_IFACE_EP;

	memcpy(usbd_state_ptr->usbd_desc_bos, usbd_desc_bos_rom, sizeof(usbd_desc_bos_rom));
	usbd_state_ptr->desc_bos.ptr = (void *)usbd_state_ptr->usbd_desc_bos;
	usbd_state_ptr->desc_bos.size = USBD_DESCSZ_BOS;

	usbd_state_ptr->usbd_desc_str0[0] = USBD_DESC_STR0_SZ;
	usbd_state_ptr->usbd_desc_str0[1] = USB_DESCTYPE_STRING;
	usbd_state_ptr->usbd_desc_str0[2] = (USBD_STR0_LANG_ID >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_str0[3] = (USBD_STR0_LANG_ID >> 8) & 0xff;
	memset(usbd_state_ptr->usbd_desc_str0 + 4, 0, sizeof(usbd_state_ptr->usbd_desc_str0) - 4);
	usbd_state_ptr->desc_str[0].ptr = (void *)usbd_state_ptr->usbd_desc_str0;
	usbd_state_ptr->desc_str[0].size = USBD_DESC_STR0_SZ;

	if (str_ind == 0) {
		usbd_state_ptr->desc_str[1].size = USBD_DESC_STR1_SZ;
		fill_str_desc(usbd_state_ptr->usbd_desc_str1, USB_DESC_ROUND_SZ(USBD_DESC_STR1_SZ),
			USBD_STR1_STR, USBD_STR1_SZ);

		usbd_state_ptr->desc_str[2].size = USBD_DESC_STR2_SZ;
		fill_str_desc(usbd_state_ptr->usbd_desc_str2, USB_DESC_ROUND_SZ(USBD_DESC_STR2_SZ),
			usbd_str2_str, USBD_STR2_SZ);
	} else {
		usbd_state_ptr->desc_str[1].size = USBD_DESC_STR1_OEM_SZ;
		fill_str_desc(usbd_state_ptr->usbd_desc_str1, USB_DESC_ROUND_SZ(USBD_DESC_STR1_OEM_SZ),
			USBD_STR1_OEM_STR, USBD_STR1_OEM_SZ);

		usbd_state_ptr->desc_str[2].size = USBD_DESC_STR2_OEM_SZ;
		fill_str_desc(usbd_state_ptr->usbd_desc_str2, USB_DESC_ROUND_SZ(USBD_DESC_STR2_OEM_SZ),
			usbd_str2_oem_str, USBD_STR2_OEM_SZ);

		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IMANUFACTURER] = 0;
		usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_IPRODUCT] = 0;
	}
	usbd_state_ptr->desc_str[1].ptr = (void *)usbd_state_ptr->usbd_desc_str1;
	usbd_state_ptr->desc_str[2].ptr = (void *)usbd_state_ptr->usbd_desc_str2;

	/* Build a serial number string from the VID and PID */
	// char str3[8];
	
	static const char str3[] = USBD_STR3_STR;

	// int2hex16(str3, cfg->serial_number);
	usbd_state_ptr->desc_str[3].ptr = (void *)usbd_state_ptr->usbd_desc_str3;
	usbd_state_ptr->desc_str[3].size = USBD_DESC_STR3_SZ;
	fill_str_desc(usbd_state_ptr->usbd_desc_str3, USB_DESC_ROUND_SZ(USBD_DESC_STR3_SZ),
		str3, USBD_STR3_SZ);

	fill_str_desc(usbd_state_ptr->usbd_desc_str_empty, USB_DESC_ROUND_SZ(USBD_DESC_STR_EMPTY_SZ),
		USBD_STR_EMPTY_STR, USBD_STR_EMPTY_SZ);
	usbd_state_ptr->desc_str_empty.size = USBD_DESC_STR_EMPTY_SZ;
	usbd_state_ptr->desc_str_empty.ptr = (void *)usbd_state_ptr->usbd_desc_str_empty;

	if (en_winusb) {
		uint8_t *ptr = winprop_build_head();

		ptr = winprop_build_prop_size(ptr, USBD_STR_MS_DEVIFACEGUID_NM,
			__builtin_strlen(USBD_STR_MS_DEVIFACEGUID_NM) + 1,
			USBD_STR_MS_DEVIFACEGUID_VAL,
			__builtin_strlen(USBD_STR_MS_DEVIFACEGUID_VAL) + 1);
		if (str_ind == 0) {
			ptr = winprop_build_prop_size(ptr, USBD_STR_MS_LABEL_NM,
				__builtin_strlen(USBD_STR_MS_LABEL_NM) + 1,
				usbd_str2_str,
				USBD_STR2_SZ + 1);
		} else {
			ptr = winprop_build_prop_size(ptr, USBD_STR_MS_LABEL_NM,
				__builtin_strlen(USBD_STR_MS_LABEL_NM) + 1,
				usbd_str2_oem_str,
				USBD_STR2_OEM_SZ + 1);
		}
		usbd_state_ptr->desc_winprop.ptr = (void *)usbd_state_ptr->usbd_desc_winprop;
		usbd_state_ptr->desc_winprop.size = ptr - usbd_state_ptr->usbd_desc_winprop;
		/* null pad */
		while (((uintptr_t)ptr & 7) != 0) {
			*ptr++ = 0;
		}

		memcpy(usbd_state_ptr->usbd_desc_wincompatid,
			usbd_desc_wincompatid_rom, sizeof(usbd_desc_wincompatid_rom));
		usbd_state_ptr->desc_wincompatid.ptr = (void *)usbd_state_ptr->usbd_desc_wincompatid;
		usbd_state_ptr->desc_wincompatid.size = USBD_DESCSZ_WINCOMPATID;

		fill_str_desc(usbd_state_ptr->usbd_desc_str_win, USB_DESC_ROUND_SZ(USBD_DESC_STR_WINDOWS_SZ),
			USBD_STR_WINDOWS_STR, USBD_STR_WINDOWS_SZ);
		usbd_state_ptr->desc_str_win.size = USBD_DESC_STR_WINDOWS_SZ;
		usbd_state_ptr->desc_str_win.ptr = (void *)usbd_state_ptr->usbd_desc_str_win;
	}
}

/* if we're operating in low-speed mode, we need to adjust the descriptors. */
void usbd_adj_descs_lowspeed(void)
{
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 0] = (USB_DEVICE_DESC_USBVER_USB1_1 >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 1] = (USB_DEVICE_DESC_USBVER_USB1_1 >> 8) & 0xff;

	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_BMAXPACKETSIZE0] = USBD_EP0_SIZE_LS;

	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 0) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 0) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE_FS >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 1) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_OUT_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 1) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_OUT_SIZE_FS >> 8) & 0xff;

#if USBD_SUPERSPEED_ENABLE
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE_FS >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					   USB_DESCSZ_INTERFACE +
					   (USB_DESCSZ_ENDPOINT * 1) +
					   USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_OUT_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					   USB_DESCSZ_INTERFACE +
					   (USB_DESCSZ_ENDPOINT * 1) +
					   USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_OUT_SIZE_FS >> 8) & 0xff;
#endif /* USBD_SUPERSPEED_ENABLE */
}

/* if we're operating in full-speed mode, we need to adjust the descriptors. */
void usbd_adj_descs_fullspeed(void)
{
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 0] = (USB_DEVICE_DESC_USBVER_USB1_1 >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 1] = (USB_DEVICE_DESC_USBVER_USB1_1 >> 8) & 0xff;

	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_BMAXPACKETSIZE0] = USBD_EP0_SIZE;

	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 0) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 0) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE_FS >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 1) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_OUT_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
					 USB_DESCSZ_INTERFACE +
					 (USB_DESCSZ_ENDPOINT * 1) +
					 USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_OUT_SIZE_FS >> 8) & 0xff;

#if USBD_SUPERSPEED_ENABLE
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE_FS >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					   USB_DESCSZ_INTERFACE +
					   (USB_DESCSZ_ENDPOINT * 1) +
					   USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_OUT_SIZE_FS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					   USB_DESCSZ_INTERFACE +
					   (USB_DESCSZ_ENDPOINT * 1) +
					   USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_OUT_SIZE_FS >> 8) & 0xff;
#endif /* USBD_SUPERSPEED_ENABLE */
}

/*
 * We might have already adjusted the descriptors for a different speed, so here we can
 * adjust the descriptors back to their high-speed defaults
 */
void usbd_adj_descs_highspeed(void)
{
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 0] = (USB_DEVICE_DESC_USBVER_USB2 >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 1] = (USB_DEVICE_DESC_USBVER_USB2 >> 8) & 0xff;

	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_BMAXPACKETSIZE0] = USBD_EP0_SIZE;

	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
				    USB_DESCSZ_INTERFACE +
				    (USB_DESCSZ_ENDPOINT * 0) +
				    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
				    USB_DESCSZ_INTERFACE +
				    (USB_DESCSZ_ENDPOINT * 0) +
				    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
				    USB_DESCSZ_INTERFACE +
				    (USB_DESCSZ_ENDPOINT * 1) +
				    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
				    USB_DESCSZ_INTERFACE +
				    (USB_DESCSZ_ENDPOINT * 1) +
				    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE >> 8) & 0xff;

#if USBD_SUPERSPEED_ENABLE
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 0) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 1) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_otherspeed_cfg[USB_DESCSZ_OTHERSPEED_CFG +
					    USB_DESCSZ_INTERFACE +
					    (USB_DESCSZ_ENDPOINT * 1) +
					    USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE >> 8) & 0xff;
#endif /* USBD_SUPERSPEED_ENABLE */
}

#if USBD_SUPERSPEED_ENABLE
/* if we're operating in super-speed mode, we need to adjust the descriptors. */
void usbd_adj_descs_superspeed(void)
{
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 0] = (USB_DEVICE_DESC_USBVER_USB3 >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_PDUSB + 1] = (USB_DEVICE_DESC_USBVER_USB3 >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_device[USB_DEVICE_DESC_OFF_BMAXPACKETSIZE0] = 9;		/* 2^9 = 512 bytes */

	usbd_state_ptr->usbd_desc_config[USB_CONFIG_DESC_OFF_WTOTALLENGTH + 0] =
		(USBD_DESCSZ_CONF_IFACE_EP_USB3 >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_CONFIG_DESC_OFF_WTOTALLENGTH + 1] =
		(USBD_DESCSZ_CONF_IFACE_EP_USB3 >> 8) & 0xff;

	/* bMaxPower (units of 8mA) */
	usbd_state_ptr->usbd_desc_config[USB_CONFIG_DESC_OFF_BMAXPOWER] = USBD_CONFIG0_MAXPOWER_MA / 8;

	uint8_t *p = usbd_state_ptr->usbd_desc_config + sizeof(usbd_desc_config_start_rom);

	memcpy(p, usbd_desc_config_usb3compan_rom, sizeof(usbd_desc_config_usb3compan_rom));
	p += sizeof(usbd_desc_config_usb3compan_rom);
	memcpy(p, usbd_desc_config_ep1_rom, sizeof(usbd_desc_config_ep1_rom));
	p += sizeof(usbd_desc_config_ep1_rom);
	memcpy(p, usbd_desc_config_usb3compan_rom, sizeof(usbd_desc_config_usb3compan_rom));
	usbd_state_ptr->desc_config.size = USBD_DESCSZ_CONF_IFACE_EP_USB3;

	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
		USB_DESCSZ_INTERFACE +
		((USB_DESCSZ_ENDPOINT + USB_DESCSZ_SS_EP_COMPANION) * 0) +
		USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_IN_SIZE_SS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
		USB_DESCSZ_INTERFACE +
		((USB_DESCSZ_ENDPOINT + USB_DESCSZ_SS_EP_COMPANION) * 0) +
		USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_IN_SIZE_SS >> 8) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
		USB_DESCSZ_INTERFACE +
		((USB_DESCSZ_ENDPOINT + USB_DESCSZ_SS_EP_COMPANION) * 1) +
		USB_EP_DESC_OFF_WMAXPACKETSIZE + 0] = (USBD_EP_BULK_OUT_SIZE_SS >> 0) & 0xff;
	usbd_state_ptr->usbd_desc_config[USB_DESCSZ_CONFIG +
		USB_DESCSZ_INTERFACE +
		((USB_DESCSZ_ENDPOINT + USB_DESCSZ_SS_EP_COMPANION) * 1) +
		USB_EP_DESC_OFF_WMAXPACKETSIZE + 1] = (USBD_EP_BULK_OUT_SIZE_SS >> 8) & 0xff;
}
#endif /* USBD_SUPERSPEED_ENABLE */
