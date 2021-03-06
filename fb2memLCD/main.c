// dispmanx to display get screenshot and send to SPI sharp memory LCD

#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <assert.h>
#include <unistd.h>
#include <sys/time.h>
#include <stdint.h>
#include <getopt.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <linux/types.h>
#include <linux/spi/spidev.h>
#include <string.h>
#include <linux/fb.h>
#include <sys/mman.h>
#include <time.h>

#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))

#include "bcm_host.h"

unsigned char reverse(unsigned char b) {
   b = (b & 0xF0) >> 4 | (b & 0x0F) << 4;
   b = (b & 0xCC) >> 2 | (b & 0x33) << 2;
   b = (b & 0xAA) >> 1 | (b & 0x55) << 1;
   return b;
}

int process()
{
    DISPMANX_DISPLAY_HANDLE_T   display;
    DISPMANX_MODEINFO_T         info;
    DISPMANX_RESOURCE_HANDLE_T  resource;
    VC_IMAGE_TYPE_T 			type = VC_IMAGE_RGB888;
    VC_IMAGE_TRANSFORM_T   		transform = 0;
    VC_RECT_T         			rect;

    uint8_t		*image;
	uint8_t 	*byteToSend;
    uint32_t 	vc_image_ptr;
	int 		BPP = 3;
    int 		ret;
    uint32_t 	screen = 0;
	int 		WIDTH = 400;
	int 		HEIGHT = 240;
	int			BYTE_WIDTH = WIDTH/8;
	int 		sizeToSend = (((WIDTH/8)+2)*HEIGHT)+2;
	int 		byteOnScreen = (WIDTH/8)*HEIGHT;
	
	int i = 0;
	int j = 0;
	uint32_t l = 0;
	uint8_t mask = 0x01;
	uint8_t bytePix = 0x00;
	int x = 0;
	int y = 0;
	int line = 0;
	uint32_t col = 0;
	int linePointer = 0;
	int screenIdx = 0;
	int lcdIdx = 0;
	uint32_t frameAlternate1 = 0;
	int slept = 0;
	long int start_time;
	long int time_difference;
	struct timespec gettime_now;
	
	int pattern[8][8] = {
    { 0, 32,  8, 40,  2, 34, 10, 42},   /* 8x8 Bayer ordered dithering  */
    {48, 16, 56, 24, 50, 18, 58, 26},   /* pattern.  Each input pixel   */
    {12, 44,  4, 36, 14, 46,  6, 38},   /* is scaled to the 0..63 range */
    {60, 28, 52, 20, 62, 30, 54, 22},   /* before looking in this table */
    { 3, 35, 11, 43,  1, 33,  9, 41},   /* to determine the action.     */
    {51, 19, 59, 27, 49, 17, 57, 25},
    {15, 47,  7, 39, 13, 45,  5, 37},
    {63, 31, 55, 23, 61, 29, 53, 21} };
	
	static const char *device = "/dev/spidev0.0";
	static uint8_t mode;
	static uint8_t bits = 8;
	static uint32_t speed = 6000000;
	static uint16_t delay = 0;
	int fd;

	clock_t t1, t2, t3, t4;

	// init SPI

	mode |= SPI_CS_HIGH;	// set CS active high
   
	fd = open(device, O_RDWR);
	if (fd < 0) {
		printf("can't open device");
		return -1;
	}
	
	ret = ioctl(fd, SPI_IOC_WR_MODE, &mode);
	if (ret == -1) {
		printf("can't set spi mode");
		return -1;
	}

	ret = ioctl(fd, SPI_IOC_RD_MODE, &mode);
	if (ret == -1) {
		printf("can't get spi mode");
		return -1;
	}

	/*
	 * bits per word
	 */
	ret = ioctl(fd, SPI_IOC_WR_BITS_PER_WORD, &bits);
	if (ret == -1) {
		printf("can't set bits per word");
		return -1;
	}

	ret = ioctl(fd, SPI_IOC_RD_BITS_PER_WORD, &bits);
	if (ret == -1) {
		printf("can't get bits per word");
		return -1;
	}

	/*
	 * max speed hz
	 */
	ret = ioctl(fd, SPI_IOC_WR_MAX_SPEED_HZ, &speed);
	if (ret == -1) printf("can't set max speed hz");

	ret = ioctl(fd, SPI_IOC_RD_MAX_SPEED_HZ, &speed);
	if (ret == -1) {
		printf("can't get max speed hz");
		return -1;
	}

	printf("Spi mode: %d\n", mode);
	printf("Bits per word: %d\n", bits);
	printf("Max speed: %d KHz\n", speed/1000);

	// prepare capture
	
    bcm_host_init();

    printf("Open display %i\n", screen );
    
	display = vc_dispmanx_display_open( screen );
    ret = vc_dispmanx_display_get_info(display, &info);
    assert(ret == 0);
    printf( "Display is %d x %d\n", info.width, info.height );

    image = malloc( sizeof(uint8_t) * info.width * BPP * info.height );
	byteToSend = malloc(sizeof(uint8_t)*sizeToSend);

    assert(image);

    resource = vc_dispmanx_resource_create( type, info.width, info.height, &vc_image_ptr );
	
	while (1) {
		// Capturing
		vc_dispmanx_snapshot(display, resource, transform);
		vc_dispmanx_rect_set(&rect, 0, 0, info.width, info.height);
		vc_dispmanx_resource_read_data(resource, &rect, image, info.width*BPP); 	
		
		// makes bytes to send on SPI
		for(line = 0; line < HEIGHT; line++){
			linePointer = line*info.width*BPP;
			byteToSend[(line*(BYTE_WIDTH+2))+1] = reverse(line+1);   //line address
			screenIdx =  linePointer;

			for(col = 0; col < BYTE_WIDTH; col++){
				bytePix = 0x00;
				for (j = 0; j < 8; j++) {		//monochorm pixel in a byte
					mask = 0b10000000 >> j;

					l = image[screenIdx++] + image[screenIdx++] + image[screenIdx++];
					l = l/3;
					l = l+1 >> 2;

					if (l > pattern[j & 7][line & 7])	// ordered dithering
						bytePix = bytePix | mask;
				}
				byteToSend[(line*(BYTE_WIDTH+2)) +col +2] = bytePix;	// image data
			}

		}

		// Command + frame alternate (com inversion)
		if (frameAlternate1%2) byteToSend[0] = 0xC0;
		else byteToSend[0] = 0x80;


		if (frameAlternate1++ == 63) {
			frameAlternate1 = 0;
		}

		// sending image block
		struct spi_ioc_transfer tr = {
			.tx_buf = (unsigned long)byteToSend,
			.rx_buf = (unsigned long)NULL,
			.len = sizeToSend,
			.delay_usecs = delay,
			.speed_hz = speed,
			.bits_per_word = bits,
		};
		
		ret = ioctl(fd, SPI_IOC_MESSAGE(1), &tr);
		if (ret < 1) {
			printf("can't send spi message");
			return -1;
		}
		
		// delay
		usleep(5000);

		slept = 0;
		while (1) {
			clock_gettime(CLOCK_REALTIME, &gettime_now);
			time_difference = gettime_now.tv_nsec - start_time;
			if (time_difference < 0)
				time_difference += 1000000000L;			// Rolls over every 1 second
			if (time_difference > (66666000L))			// Delay for 15 fps
				break;
			slept++;
			usleep(2000);
		}
		clock_gettime(CLOCK_REALTIME, &gettime_now);
		start_time = gettime_now.tv_nsec;		//Get nS value

		printf("%d\n", slept);

	}
	
	
	// cleanup
    free(byteToSend);
	close(fd);
	
	ret = vc_dispmanx_resource_delete( resource );
    assert( ret == 0 );
    ret = vc_dispmanx_display_close(display );
    assert( ret == 0 );
    

    return 0;
}

int main(int argc, char **argv) {
    return process();
}
