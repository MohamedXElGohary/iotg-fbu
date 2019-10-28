/*
 * {% copyright %}
 */

#ifndef __MA_USBD_SETUP_DESCRIPTORS_H__
#define __MA_USBD_SETUP_DESCRIPTORS_H__

/*
 * The number of bytes for our full configuration descriptor,
 * including the interface descriptor and endpoint descriptors.
 */
#define USBD_DESCSZ_CONF_IFACE_EP_USB2 (USB_DESCSZ_CONFIG + \
				       (USBD_INTERFACE_COUNT * USB_DESCSZ_INTERFACE) + \
				       (USBD_EP_BULK_CNT * USB_DESCSZ_ENDPOINT))
#define USBD_DESCSZ_CONF_IFACE_EP_USB3 (USB_DESCSZ_CONFIG + \
				       (USBD_INTERFACE_COUNT * USB_DESCSZ_INTERFACE) + \
				       (USBD_EP_BULK_CNT * USB_DESCSZ_ENDPOINT) + \
				       (USBD_EP_BULK_CNT * USB_DESCSZ_SS_EP_COMPANION))

#define USBD_DESCSZ_OTHERSPEED_IFACE_EP (USB_DESCSZ_OTHERSPEED_CFG + \
					(USBD_INTERFACE_COUNT * USB_DESCSZ_INTERFACE) + \
					(USBD_EP_BULK_CNT * USB_DESCSZ_ENDPOINT))

#define USBD_DESCSZ_WINCOMPATID     (40)

/* Round up a descriptor size to the nearest 8 bytes. */
#define USB_DESC_ROUND_SZ(x)        (((x) + 7) & ~7)

/* Allow a 16-bit value to be inserted into a byte array. */
#define PW(x)       ((x) & 0xff), (((x) >> 8) & 0xff)
/* Allow a 32-bit value to be inserted into a byte array. */
#define PD(x)       PW(x), PW(x >> 16)

#define MA_USBD_MAX(x, y)                        (((x) > (y)) ? (x) : (y))

/* Calculate the size of a string descriptor. */
#define USB_STR_DESC_SZ(str)            (2 + (__builtin_strlen(str) * 2))

/* Size of string descriptor 0 (language ID(s)). */
#define USBD_DESC_STR0_SZ               (2 + sizeof(uint16_t))

#define USBD_STR1_STR                   USBD_STR_MANUFACTURER
#define USBD_STR1_OEM_STR               USBD_STR_MANUFACTURER_OEM
#define USBD_STR2_STR                   USBD_STR_PRODUCT
#define USBD_STR2_OEM_STR               USBD_STR_PRODUCT_OEM
#define USBD_STR3_STR                   "FA57B007B04D0007"           // not the real string
#define USBD_STR_EMPTY_STR              ""

#define USBD_STR1_SZ                    __builtin_strlen(USBD_STR1_STR)
#define USBD_STR1_OEM_SZ                __builtin_strlen(USBD_STR1_OEM_STR)
#define USBD_STR2_SZ                    __builtin_strlen(USBD_STR2_STR)
#define USBD_STR2_OEM_SZ                __builtin_strlen(USBD_STR2_OEM_STR)
#define USBD_STR3_SZ                    __builtin_strlen(USBD_STR3_STR)
#define USBD_STR_EMPTY_SZ               __builtin_strlen(USBD_STR_EMPTY_STR)
#define USBD_STR_WINDOWS_SZ             (8)

#define USBD_DESC_STR1_SZ               USB_STR_DESC_SZ(USBD_STR1_STR)
#define USBD_DESC_STR1_OEM_SZ           USB_STR_DESC_SZ(USBD_STR1_OEM_STR)
#define USBD_DESC_STR2_SZ               USB_STR_DESC_SZ(USBD_STR2_STR)
#define USBD_DESC_STR2_OEM_SZ           USB_STR_DESC_SZ(USBD_STR2_OEM_STR)
#define USBD_DESC_STR3_SZ               USB_STR_DESC_SZ(USBD_STR3_STR)
#define USBD_DESC_STR_EMPTY_SZ          USB_STR_DESC_SZ(USBD_STR_EMPTY_STR)
#define USBD_DESC_STR_WINDOWS_SZ        ((USBD_STR_WINDOWS_SZ * 2) + 2)

/* We need enough space to fit either the normal strings or the 'OEM' strings. */
#define USBD_DESC_STR1_SZ_MAX           MA_USBD_MAX(USBD_DESC_STR1_SZ, USBD_DESC_STR1_OEM_SZ)
#define USBD_DESC_STR2_SZ_MAX           MA_USBD_MAX(USBD_DESC_STR2_SZ, USBD_DESC_STR2_OEM_SZ)

#define USBD_DESC_WINPROP_HEADERSZ      (10)
#define USBD_DESC_WINPROP_PROPSTRUCT_SIZE (14)          // not including data

#define USBD_DESC_WINPROP_PROP_SZ(nm, val)      (USBD_DESC_WINPROP_PROPSTRUCT_SIZE + \
						((__builtin_strlen(nm) + 1) * 2) + \
						((__builtin_strlen(val) + 1) * 2))

#define USBD_DESCSZ_WINPROP (USBD_DESC_WINPROP_HEADERSZ + \
			     USBD_DESC_WINPROP_PROP_SZ(USBD_STR_MS_DEVIFACEGUID_NM, USBD_STR_MS_DEVIFACEGUID_VAL) + \
			     USBD_DESC_WINPROP_PROP_SZ(USBD_STR_MS_LABEL_NM, USBD_STR_MS_LABEL_VAL))

#define USBD_DESCSZ_BOS (USB_DESCSZ_BOS + USB_DESCSZ_DEVCAP_USB2EXTENSION + USB_DESCSZ_DEVCAP_SUPERSPEEDUSB)

#endif /* __MA_USBD_SETUP_DESCRIPTORS_H__ */
