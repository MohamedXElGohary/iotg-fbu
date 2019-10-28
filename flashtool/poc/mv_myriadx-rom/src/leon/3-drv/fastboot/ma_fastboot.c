/*
 * {% copyright %}
 */

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <soc_def.h>
#include <ma_fastboot.h>
#include <ma_usbd_config.h>
#include <ma_timer.h>

#if !IMAGE_MA2X8X
#include <string.h>
#include <debug.h>
#endif /* !IMAGE_MA2X8X */

#define FASTBOOT_COMMAND_SIZE 64
#define FASTBOOT_RESPONSE_SIZE 64
/* Use max size of the USB endpoint buffer. */
#define FASTBOOT_BUFFER_SIZE (USBD_BUFF_OUT_LEN)
#define FASTBOOT_STRING_MAX_LENGTH 256
#define FASTBOOT_DOWNLOAD_MAX_LENGTH 8
#define FASTBOOT_MIN_RESPONSE_SIZE 4

#define FASTBOOT_RESPONSE_OKAY "OKAY"
#define FASTBOOT_RESPONSE_FAIL "FAIL"
#define FASTBOOT_RESPONSE_DATA "DATA"
#define FASTBOOT_RESPONSE_INFO "INFO"

#define FASTBOOT_COMMAND_GETVAR "getvar"
#define FASTBOOT_COMMAND_DOWNLOAD "download"
#define FASTBOOT_COMMAND_UPLOAD "upload"
#define FASTBOOT_COMMAND_FLASH "flash"
#define FASTBOOT_COMMAND_ERASE "erase"
#define FASTBOOT_COMMAND_BOOT "boot"
#define FASTBOOT_COMMAND_CONTINUE "continue"
#define FASTBOOT_COMMAND_REBOOT "reboot"
#define FASTBOOT_COMMAND_REBOOT_BOOTLOADER "reboot-bootloader"

#define FASTBOOT_VARIABLE_VERSION "version"
#define FASTBOOT_VARIABLE_VERSION_BOOTLOADER "version-bootloader"
#define FASTBOOT_VARIABLE_VERSION_BASEBAND "version-baseband"
#define FASTBOOT_VARIABLE_PRODUCT "product"
#define FASTBOOT_VARIABLE_SERIALNO "serialno"
#define FASTBOOT_VARIABLE_SECURE "secure"
#define FASTBOOT_VARIABLE_IS_USERSPACE "is-userspace"
#define FASTBOOT_VARIABLE_MAX_DOWNLOAD_SIZE "max-download-size"

/* Flash partitions. */
#define FASTBOOT_PARTITION_BOOTLOADER "boot"
#define FASTBOOT_PARTITION_SYSTEM "system"


/* Platform specfic. */
#define FASTBOOT_VARIABLE_BOOTSTAGE "Bootstage"
#define FASTBOOT_VARIABLE_RECOVERY "Recovery"

/* TODO - JHD - Move these strings outside FastBoot. */
#define FASTBOOT_PRODUCT "Intel Movidius Keembay 3xxx"
#define FASTBOOT_VERSION_BOOTLOADER "1.0"

#define FASTBOOT_VERSION "0.4"
#define FASTBOOT_VERSION_BASEBAND "N/A"

typedef enum {
	EXPECT_COMMAND_STATE,
	EXPECT_DATA_STATE,
	FASTBOOT_STATE_MAX
} fastboot_state_t;

static fastboot_state_t fastboot_state;

typedef enum {
	DATA_NOT_STAGED = 0,
	DATA_STAGED
} fastboot_data_staged_t;

static fastboot_data_staged_t fastboot_data_staged;

/* Used to incidcate if a continue command has been received. */
typedef enum {
	CONTINUE_NOT_RECEIVED = 0,
	CONTINUE_RECEIVED
} fastboot_continue_t;

static fastboot_continue_t fastboot_continue;

/* Used to incidcate if the WDT has been already tickled. */
typedef enum {
	WDT_NOT_TICKLED = 0,
	WDT_TICKLED
} wdt_tickle_t;

static wdt_tickle_t wdt_tickle;

/* When in EXPECT_DATA_STATE, the number of bytes of data to expect: */
static unsigned int num_data_bytes;

/* .. and the number of bytes so far received this data phase. */
static unsigned int bytes_received_so_far;

#define PARSE(str, buf) !strncmp(str, buf, sizeof(str) - 1)
#define IS_LOWERCASE_ASCII(c) ((c >= 'a') && (c <= 'z'))

static char download_size_buf[FASTBOOT_DOWNLOAD_MAX_LENGTH];

static char block[FASTBOOT_BUFFER_SIZE];

static int hex2uint(const char *const in, const unsigned int len, unsigned int *const out);
static void send_response(const ma_fastboot_cfg_t * const config, const char *const str);
static void handle_get_var(const ma_fastboot_cfg_t * const config, const char *const arg);
static void handle_flash(const ma_fastboot_cfg_t * const config, const char *const arg);
static void handle_download(const ma_fastboot_cfg_t * const config, const char *const arg);
#if (!IMAGE_BL1 && DEBUG)
static void handle_upload(const ma_fastboot_cfg_t * const config);
#endif /* (!IMAGE_BL1 && DEBUG) */
static void fastboot_spis(const ma_fastboot_cfg_t * const config);
static void fastboot_usb(const ma_fastboot_cfg_t * const config);
static void fastboot_handle_command(const ma_fastboot_cfg_t * const config, const unsigned int size);
static void fastboot_handle_data(const ma_fastboot_cfg_t * const config, const unsigned int size);

/* TODO - Code to be removed after PO. */
#if IMAGE_MA2X8X
LOAD_BSS_NOZERO_1(fastboot_state);
LOAD_BSS_NOZERO_1(fastboot_data_staged);
LOAD_BSS_NOZERO_1(fastboot_continue);
LOAD_BSS_NOZERO_1(num_data_bytes);
LOAD_BSS_NOZERO_1(wdt_tickle);
LOAD_BSS_NOZERO_1(bytes_received_so_far);
LOAD_BSS_NOZERO_1(download_size_buf);
LOAD_BSS_NOZERO_1(block);
#endif

/***************************************/
/* Entry point of the FastBoot driver. */
/***************************************/
int ma_fastboot(const ma_fastboot_cfg_t * const config)
{
	fastboot_continue = CONTINUE_NOT_RECEIVED;
	wdt_tickle = WDT_NOT_TICKLED;

	if (config != NULL) {
		/* Check the configuration parameters. */
		if (config->getchar == NULL) {
			return -EINVAL;
		}

		if (config->putchar == NULL) {
			return -EINVAL;
		}

		if (config->getblock == NULL) {
			return -EINVAL;
		}

		if (config->getavail == NULL) {
			return -EINVAL;
		}

		switch (config->transport) {
		case MA_FASTBOOT_USB:
			if (config->process == NULL) {
				return -EINVAL;
			}

			fastboot_usb(config);
			break;
		case MA_FASTBOOT_SPIS:
			if (config->prep_response == NULL) {
				return -EINVAL;
			}

			if (config->read == NULL) {
				return -EINVAL;
			}

			fastboot_spis(config);
			break;
		default:
			/* Passthrough */
			break;
		}
	}

	/* Only exit fastboot when a continue command has been received. */
	return 0;
}

static int hex2uint(const char *const in, const unsigned int len, unsigned int *const out)
{
	unsigned int i = 0;
	unsigned int val = 0;

	if (!in) {
		return -EINVAL;
	}

	for (i = 0; i < len; i++) {
		if ((in[i] <= '9') && (in[i] >= '0')) {
			val += (in[i] - '0') * (1 << (4 * (len - 1 - i)));
		} else if ((in[i] >= 'a') && (in[i] <= 'f')) {
			val += ((in[i] - 'a') + 10) * (1 << (4 * (len - 1 - i)));
		} else if ((in[i] >= 'A') && (in[i] <= 'F')) {
			val += ((in[i] - 'A') + 10) * (1 << (4 * (len - 1 - i)));
		} else {
			return -EINVAL;
		}
	}

	*out = val;

	return 0;
}

static void send_response(const ma_fastboot_cfg_t * const config, const char *const str)
{
	unsigned int size = (unsigned int)strlen(str);
	unsigned int i = 0;
	const char *msg = str;
	const char err_resp[] = FASTBOOT_RESPONSE_FAIL "DeviceError";

	if (config->transport == MA_FASTBOOT_SPIS) {
		if (config->prep_response() != 0) {
			ERROR("SPI Slave failed to prepare for TX\n");
		}
	}

	if (size > FASTBOOT_RESPONSE_SIZE) {
		size = sizeof(err_resp);
		msg = (char *)err_resp;
	}

	for (i = 0; i < size; i++) {
		config->putchar(msg[i]);
	}

	if (config->transport == MA_FASTBOOT_USB) {
		config->process();
	} else if (config->transport == MA_FASTBOOT_SPIS) {
		/* Pad out response for fastboot SPI host */
		for (i = 0; i < (FASTBOOT_RESPONSE_SIZE - size); i++) {
			config->putchar('\0');
		}
	}

	INFO("Resp: %s\n", msg);
}

static void handle_get_var(const ma_fastboot_cfg_t * const config, const char *const arg)
{
	bool is_enabled = false;

	if (PARSE(FASTBOOT_VARIABLE_VERSION, arg)) {
		if (PARSE(FASTBOOT_VARIABLE_VERSION_BOOTLOADER, arg)) {
			send_response(config, FASTBOOT_RESPONSE_OKAY FASTBOOT_VERSION_BOOTLOADER);
		} else if (PARSE(FASTBOOT_VARIABLE_VERSION_BASEBAND, arg)) {
			send_response(config, FASTBOOT_RESPONSE_OKAY FASTBOOT_VERSION_BASEBAND);
		} else {
			/* Respond to getvar:version with 0.4 (version of Fastboot protocol). */
			send_response(config, FASTBOOT_RESPONSE_OKAY FASTBOOT_VERSION);
		}
	} else if (PARSE(FASTBOOT_VARIABLE_PRODUCT, arg)) {
		send_response(config, FASTBOOT_RESPONSE_OKAY FASTBOOT_PRODUCT);
	} else if (PARSE(FASTBOOT_VARIABLE_SERIALNO, arg)) {
		unsigned int i = 0;
		unsigned int var = 0;
		unsigned int nb_byte = config->data.serial_number_size;
		char response[FASTBOOT_RESPONSE_SIZE + 1] = FASTBOOT_RESPONSE_OKAY;

		if ((config->data.serial_number == NULL) || (config->data.serial_number_size == 0)) {
			send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
			return;
		}

		/* Check that serial number size is not greater than size of response stack buffer */
		if ((nb_byte << 1) > (FASTBOOT_RESPONSE_SIZE - FASTBOOT_MIN_RESPONSE_SIZE)) {
			send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
			return;
		}

		/* Append the DeviceID to the OKAY string as hex characters */
		for (i = 0; i < nb_byte; i++) {
			var = config->data.serial_number[i];
			if ((var >> 4) <= 9) {
				response[FASTBOOT_MIN_RESPONSE_SIZE + (i * 2)] = (var >> 4) + '0';
			} else {
				response[FASTBOOT_MIN_RESPONSE_SIZE + (i * 2)] = (var >> 4) - 0x0A + 'A';
			}
			if ((var & 0x0f) <= 9) {
				response[FASTBOOT_MIN_RESPONSE_SIZE + (i * 2) + 1] = (var & 0x0f) + '0';
			} else {
				response[FASTBOOT_MIN_RESPONSE_SIZE + (i * 2) + 1] = (var & 0x0f) - 0x0A + 'A';
			}
		}

		/* Add NULL termination. */
		response[FASTBOOT_MIN_RESPONSE_SIZE + (nb_byte << 1)] = '\0';

		send_response(config, response);
	} else if (PARSE(FASTBOOT_VARIABLE_SECURE, arg)) {
		is_enabled = SOC_BOOT_FLAG_IS_SECURE_BOOT_EN();
		if (is_enabled) {
			send_response(config, FASTBOOT_RESPONSE_OKAY "yes");
		} else if (!is_enabled) {
			send_response(config, FASTBOOT_RESPONSE_OKAY "no");
		}
	} else if (PARSE(FASTBOOT_VARIABLE_IS_USERSPACE, arg)) {
		send_response(config, FASTBOOT_RESPONSE_OKAY "no");
	} else if (PARSE(FASTBOOT_VARIABLE_MAX_DOWNLOAD_SIZE, arg)) {
		unsigned int i = 0;
		unsigned int j = 0;
		unsigned int r = 0;
		unsigned int num_digits = 0;
		unsigned int size = config->data.max_download_size;
		char response[FASTBOOT_RESPONSE_SIZE + 1] = FASTBOOT_RESPONSE_OKAY;

		/* Count number of digits to append after OKAY. */
		j = size;
		while (j != 0) {
			num_digits += 1;
			j /= 10;
		}

		/* Check that resulting response is not greater than size of response stack buffer */
		if (num_digits > (FASTBOOT_RESPONSE_SIZE - FASTBOOT_MIN_RESPONSE_SIZE)) {
			send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
			return;
		}

		if (num_digits == 0) {
			/* Append only one digit, 0. */
			response[FASTBOOT_MIN_RESPONSE_SIZE] = '0';

			/* Add NULL termination. */
			response[FASTBOOT_MIN_RESPONSE_SIZE + 1] = '\0';
		} else {
			/* Append the SOC_FIP_MAX_SIZE after the OKAY, in decimal. */
			for (i = 0, j = num_digits - 1; i < num_digits; i++, j--) {
				r = size % 10;

				response[FASTBOOT_MIN_RESPONSE_SIZE + j] = r + '0';
				size = size / 10;
			}

			/* Add NULL termination. */
			response[FASTBOOT_MIN_RESPONSE_SIZE + num_digits] = '\0';
		}

		send_response(config, response);

	} else if (PARSE(FASTBOOT_VARIABLE_BOOTSTAGE, arg)) {

/* TODO - JHD - Move these strings outside FastBoot. */
#if IMAGE_BL1
		send_response(config, FASTBOOT_RESPONSE_OKAY "bl1");
#endif /* IMAGE_BL1 */
#if IMAGE_BL2
		send_response(config, FASTBOOT_RESPONSE_OKAY "bl2");
#endif /* IMAGE_BL2 */
#if IMAGE_BL31
		send_response(config, FASTBOOT_RESPONSE_OKAY "bl31");
#endif /* IMAGE_BL31 */
#if IMAGE_BL32
		send_response(config, FASTBOOT_RESPONSE_OKAY "bl32");
#endif /* IMAGE_BL32 */
#if IMAGE_BL33
		send_response(config, FASTBOOT_RESPONSE_OKAY "bl33");
#endif /* IMAGE_BL33 */
#if IMAGE_MA2X8X
		send_response(config, FASTBOOT_RESPONSE_OKAY "ma2x8x");
#endif /* IMAGE_MA2X8X */
	} else if (PARSE(FASTBOOT_VARIABLE_RECOVERY, arg)) {
		is_enabled = SOC_BOOT_FLAG_IS_RECOVERY_SIGNALED();
		if (is_enabled) {
			send_response(config, FASTBOOT_RESPONSE_OKAY "yes");
		} else if (!is_enabled) {
			send_response(config, FASTBOOT_RESPONSE_OKAY "no");
		}
	} else {
		/* All other variables are assumed to be platform specific. */
		send_response(config, FASTBOOT_RESPONSE_FAIL "Variable not found");
	}
}

static void handle_download(const ma_fastboot_cfg_t * const config, const char *const arg)
{
	char response[FASTBOOT_RESPONSE_SIZE + 1] = FASTBOOT_RESPONSE_DATA;
	unsigned int i = 0;
	const unsigned int len = (unsigned int)strlen(arg);

	if (len > (FASTBOOT_BUFFER_SIZE - sizeof(FASTBOOT_COMMAND_DOWNLOAD))) {
		/* Potential buffer overflow */
		return;
	}

	/* Parse out number of data bytes to expect. */
	if (hex2uint(arg, len, &num_data_bytes) < 0) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Number error");
		return;
	}

	/* Parsing error or no data requested */
	if (num_data_bytes == 0) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Zero download size");
		return;
	}

	/* Compare to the buffer max size. */
	if (num_data_bytes > SOC_FIP_MAX_SIZE) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Not enough memory");
	} else {
		for (i = 0; i < len; i++) {
			response[FASTBOOT_MIN_RESPONSE_SIZE + i] = arg[i];
			/* Save the size for upload use. */
			download_size_buf[i] = arg[i];
		}
		send_response(config, response);

		fastboot_state = EXPECT_DATA_STATE;
		bytes_received_so_far = 0;

		if (config->transport == MA_FASTBOOT_SPIS) {
			if (config->read((uintptr_t)config->data.stage_buffer, num_data_bytes) != num_data_bytes) {
				ERROR("Failed to download full FIP");
				send_response(config, FASTBOOT_RESPONSE_FAIL);
			} else {
				/* All done. */
				send_response(config, FASTBOOT_RESPONSE_OKAY);
#if IMAGE_BL1
				/* Exit the FastBoot mode. */
				fastboot_continue = CONTINUE_RECEIVED;
#endif /* IMAGE_BL1 */
			}

			/* Outside of BL1 we may wait for another command before exiting */
			fastboot_state = EXPECT_COMMAND_STATE;
		}
	}
}

#if (!IMAGE_BL1 && DEBUG)
static void handle_upload(const ma_fastboot_cfg_t * const config)
{
	unsigned int i = 0;
	char response[FASTBOOT_RESPONSE_SIZE + 1] = FASTBOOT_RESPONSE_DATA;
	char *const buf = (char *)(config->data.stage_buffer);

	/* Check if a download has been made before. */
	if (fastboot_data_staged == DATA_STAGED) {
		/* Add back the download size to the response. */
		for (i = 0; i < FASTBOOT_DOWNLOAD_MAX_LENGTH; i++) {
			response[FASTBOOT_MIN_RESPONSE_SIZE + i] = download_size_buf[i];
		}
		send_response(config, response);

		/* Send the content of the staged buffer. */
		for (i = 0; i < num_data_bytes; i++) {
			config->putchar(buf[i]);
		}

		if (config->transport == MA_FASTBOOT_USB) {
			config->process();
		}

		/* All done. */
		send_response(config, FASTBOOT_RESPONSE_OKAY);
	} else {
		send_response(config, FASTBOOT_RESPONSE_FAIL);
	}
}
#endif /* (!IMAGE_BL1 && DEBUG) */

static void fastboot_spis(const ma_fastboot_cfg_t * const config)
{
	unsigned int size = 0;

	/* Debug info */
	INFO("Fastboot download over SPI Slave\n");
	INFO("\tSerial number lwr: 0x%x\n", (unsigned int)(*(uintptr_t *)((config->data.serial_number))));
	INFO("\tSerial number upr: 0x%x\n", (unsigned int)(*(uintptr_t *)((config->data.serial_number + 4))));
	INFO("\tSerial number size: 0x%x\n", (unsigned int)(config->data.serial_number_size));
	INFO("\tStage buffer: 0x%lx\n", ((uintptr_t)(config->data.stage_buffer)));
	INFO("\tMax download size: 0x%x\n", (unsigned int)(config->data.max_download_size));

	fastboot_state = EXPECT_COMMAND_STATE;
	fastboot_data_staged = DATA_NOT_STAGED;

	/* Only exit this while loop if a continue command has been received. */
	while (fastboot_continue == CONTINUE_NOT_RECEIVED) {
		/* Wait until a block of data is available, and get its size. */
		size = config->getavail();

		if (size != 0) {
			if (fastboot_state == EXPECT_COMMAND_STATE) {
				fastboot_handle_command(config, size);
			}
		}
	}
}

static void fastboot_usb(const ma_fastboot_cfg_t * const config)
{
	unsigned int size = 0;

	fastboot_state = EXPECT_COMMAND_STATE;
	fastboot_data_staged = DATA_NOT_STAGED;

	/* Only exit this while loop if a continue command has been received. */
	while (fastboot_continue == CONTINUE_NOT_RECEIVED) {
		/* Wait until a block of data is available, and get its size. */
		size = config->getavail();

		if (size != 0) {
			if (fastboot_state == EXPECT_COMMAND_STATE) {
				fastboot_handle_command(config, size);
			} else if (fastboot_state == EXPECT_DATA_STATE) {
				fastboot_handle_data(config, size);
			}
		}
	}
}

static void fastboot_handle_command(const ma_fastboot_cfg_t * const config, const unsigned int size)
{
	/* Max command size is 64 bytes. */
	if (size > FASTBOOT_COMMAND_SIZE) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Command too large");
		/* Quit this function, but don't leave the main fastboot while(1) loop. */
		return;
	}

	config->getblock(&block, size);

	/* Commands are not null-terminated, add a null-termination to help on parsing. */
	block[size] = '\0';

	INFO("Cmd: %s\n", block);

	/* Parse the command. */
	if (PARSE(FASTBOOT_COMMAND_GETVAR, block)) {
		handle_get_var(config, block + sizeof(FASTBOOT_COMMAND_GETVAR));
	} else if (PARSE(FASTBOOT_COMMAND_DOWNLOAD, block)) {
		handle_download(config, block + sizeof(FASTBOOT_COMMAND_DOWNLOAD));
	} else if (PARSE(FASTBOOT_COMMAND_UPLOAD, block)) {
#if (!IMAGE_BL1 && DEBUG)
		handle_upload(config);
#else /* (!IMAGE_BL1 && DEBUG) */
		/* Security: BL1-ROM never to support upload of collateral to external host. */
		send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
#endif /* (!IMAGE_BL1 && DEBUG) */
	} else if (PARSE(FASTBOOT_COMMAND_ERASE, block)) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
	} else if (PARSE(FASTBOOT_COMMAND_FLASH, block)) {
		// send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
		handle_flash(config, block + sizeof(FASTBOOT_COMMAND_FLASH));
	} else if (PARSE(FASTBOOT_COMMAND_BOOT, block)) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
	} else if (PARSE(FASTBOOT_COMMAND_CONTINUE, block)) {
		send_response(config, FASTBOOT_RESPONSE_OKAY);
		fastboot_continue = CONTINUE_RECEIVED;
		/* Quit this function with the right continue status. */
		return;
	} else if (PARSE(FASTBOOT_COMMAND_REBOOT, block)) {
#if !IMAGE_BL1
		if (PARSE(FASTBOOT_COMMAND_REBOOT_BOOTLOADER, block)) {
			send_response(config,
			FASTBOOT_RESPONSE_INFO "reboot-bootloader not supported, rebooting normally.");
		}
		/* Force a WDT reset. */
		ma_wdt_refresh(SOC_TIMER_BASE, 0);
#else /* !IMAGE_BL1 */
		send_response(config, FASTBOOT_RESPONSE_FAIL "Not supported");
#endif /* !IMAGE_BL1 */
	} else if (IS_LOWERCASE_ASCII(block[0])) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Command not recognised. Check Fastboot version.");
	} else {
		send_response(config, FASTBOOT_RESPONSE_FAIL "Command not recognised.");
	}

	if (wdt_tickle == WDT_NOT_TICKLED) {
		/* Tickle the WDT after a first command. */
		ma_wdt_refresh(SOC_TIMER_BASE, (SOC_WDT_RESET_TIMEOUT_TICKS >> 1));
		wdt_tickle = WDT_TICKLED;
	}
}

static void fastboot_handle_data(const ma_fastboot_cfg_t * const config, const unsigned int size)
{
	unsigned int tmp_size = size;
	unsigned int remaining_bytes = num_data_bytes - bytes_received_so_far;

	/* Protocol doesn't say anything about sending extra data so just ignore it. */
	if (tmp_size > remaining_bytes) {
		tmp_size = remaining_bytes;
	}

	/* Copy the received data into the memory destination. */
	config->getblock(config->data.stage_buffer + bytes_received_so_far, tmp_size);

	bytes_received_so_far += tmp_size;
	if (bytes_received_so_far >= num_data_bytes) {
		/* Download finished. */
		send_response(config, FASTBOOT_RESPONSE_OKAY);
		fastboot_state = EXPECT_COMMAND_STATE;
		fastboot_data_staged = DATA_STAGED;
#ifdef IMAGE_BL1
		/* Exit the FastBoot mode. */
		fastboot_continue = CONTINUE_RECEIVED;
#endif /* IMAGE_BL1 */
	}
}

static void handle_flash(const ma_fastboot_cfg_t * const config, const char *const arg)
{

	if (PARSE(FASTBOOT_PARTITION_BOOTLOADER, arg)) {
		int i;
		for (i=1; i<=10; i++) {
			MA_USBD_UDELAY(1000000);
		}
        send_response(config, FASTBOOT_RESPONSE_OKAY);
	} else if (PARSE(FASTBOOT_PARTITION_SYSTEM, arg)) {
		send_response(config, FASTBOOT_RESPONSE_FAIL "not implemented");
	}  else {
		/* All other variables are assumed to be platform specific. */
		send_response(config, FASTBOOT_RESPONSE_FAIL "unknown partition");
	}
}

